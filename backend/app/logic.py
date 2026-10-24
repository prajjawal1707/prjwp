from functools import lru_cache
from pathlib import Path
import pandas as pd

LONDON = "Europe/London"
DATA = Path(__file__).resolve().parent.parent / "data"

# Delivery days whose day-ahead decision falls in January 2026 (decision is on D-1)
MIN_DAY = "2026-01-02"
MAX_DAY = "2026-02-01"
FORECAST_STEP_H = 1.0     # WINDFOR is hourly
POINTS_PER_DAY = 24


# ---------- loading ----------
@lru_cache(maxsize=1)
def load():
    act = pd.read_csv(DATA / "actuals.csv")
    fc = pd.read_csv(DATA / "forecasts.csv")
    act["startTime"] = pd.to_datetime(act["startTime"], utc=True)
    fc["startTime"] = pd.to_datetime(fc["startTime"], utc=True)
    fc["publishTime"] = pd.to_datetime(fc["publishTime"], utc=True)
    return act, fc


def _iso(s):
    return s.dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _records(df):
    """DataFrame -> JSON-safe records (NaN -> None)."""
    return df.astype(object).where(df.notna(), None).to_dict("records")


def _cutoff_ts(day, cutoff):
    """Decision time: `cutoff` London time on the day BEFORE delivery `day`."""
    naive = pd.Timestamp(f"{day} {cutoff}") - pd.Timedelta(days=1)
    return naive.tz_localize(LONDON)


def _day_bounds(day):
    start = pd.Timestamp(day).tz_localize(LONDON)
    end = (pd.Timestamp(day) + pd.Timedelta(days=1)).tz_localize(LONDON)
    return start, end


# ---------- forecast selection ----------
def decision_forecast(fc, day, cutoff="09:00"):
    """Latest forecast per half-hour published at or before the decision cutoff."""
    day_start, day_end = _day_bounds(day)
    cutoff_ts = _cutoff_ts(day, cutoff)
    valid = fc[(fc.startTime >= day_start) & (fc.startTime < day_end)
               & (fc.publishTime <= cutoff_ts)]
    latest = valid.sort_values("publishTime").groupby("startTime").last().reset_index()
    return latest.rename(columns={"generation": "forecast"})


def latest_forecast(fc, day):
    """Hindsight only: newest forecast published before delivery starts.
    NOT available when the purchase decision is made."""
    day_start, day_end = _day_bounds(day)
    valid = fc[(fc.startTime >= day_start) & (fc.startTime < day_end)
               & (fc.publishTime <= day_start)]
    latest = valid.sort_values("publishTime").groupby("startTime").last().reset_index()
    return latest.rename(columns={"generation": "forecast_latest"})


# ---------- comparison + metrics ----------
EMPTY_COLS = ["startTime", "publishTime", "forecast", "actual", "error", "horizon_h"]


def compare(date_from, date_to, cutoff="09:00"):
    act, fc = load()
    parts = [decision_forecast(fc, d.strftime("%Y-%m-%d"), cutoff)
             for d in pd.date_range(date_from, date_to)]
    parts = [p for p in parts if not p.empty]
    if not parts:
        return pd.DataFrame(columns=EMPTY_COLS)
    f = pd.concat(parts, ignore_index=True)
    a = act.rename(columns={"generation": "actual"})
    df = f.merge(a, on="startTime", how="inner")
    df["error"] = df["forecast"] - df["actual"]          # + = over-forecast
    df["horizon_h"] = (df["startTime"] - df["publishTime"]).dt.total_seconds() / 3600
    return df.sort_values("startTime").reset_index(drop=True)


def _stats(e, actual=None):
    abs_e = e.abs()
    out = {
        "n": int(len(e)),
        "mae": float(abs_e.mean()),
        "rmse": float((e ** 2).mean() ** 0.5),
        "bias": float(e.mean()),
        "p90_abs_error": float(abs_e.quantile(0.9)),
    }
    if actual is not None and actual.mean() != 0:
        out["nmae_pct"] = float(abs_e.mean() / actual.mean() * 100)
    return out


def metrics(df):
    if df.empty:
        return {"n": 0, "mae": None, "rmse": None, "bias": None,
                "p90_abs_error": None, "nmae_pct": None}
    return _stats(df["error"], df["actual"])


def _grouped(df, key):
    if df.empty:
        return []
    rows = []
    for k, g in df.groupby(key, sort=True):
        s = _stats(g["error"])
        s["key"] = k if isinstance(k, str) else int(k)
        rows.append(s)
    return rows


def by_hour(df):
    if df.empty:
        return []
    d = df.copy()
    d["k"] = d["startTime"].dt.tz_convert(LONDON).dt.hour
    return _grouped(d, "k")


def by_horizon(df, bucket=3):
    if df.empty:
        return []
    d = df.copy()
    lo = (d["horizon_h"] // bucket * bucket).astype(int)
    d["k"] = lo.astype(str) + "-" + (lo + bucket).astype(str) + "h"
    rows = _grouped(d, "k")
    rows.sort(key=lambda r: int(r["key"].split("-")[0]))
    return rows


def by_day(df):
    if df.empty:
        return []
    d = df.copy()
    d["k"] = d["startTime"].dt.tz_convert(LONDON).dt.strftime("%Y-%m-%d")
    return _grouped(d, "k")


# ---------- decision view ----------
def error_band(day, cutoff):
    """P90 absolute error using only days whose actuals were fully known at decision
    time (<= D-2), so there is no look-ahead."""
    last = (pd.Timestamp(day) - pd.Timedelta(days=2)).strftime("%Y-%m-%d")
    if last < MIN_DAY:
        return None
    h = compare(MIN_DAY, last, cutoff)
    if h.empty:
        return None
    return {"p90": float(h["error"].abs().quantile(0.9)),
            "mae": float(h["error"].abs().mean()),
            "throughDay": last, "points": int(len(h))}


def decision(day, cutoff="09:00"):
    act, fc = load()
    d = decision_forecast(fc, day, cutoff)
    late = latest_forecast(fc, day).rename(columns={"publishTime": "latestPublishTime"})
    a = act.rename(columns={"generation": "actual"})
    out = d.merge(late, on="startTime", how="left").merge(a, on="startTime", how="left")

    meta = {
        "deliveryDay": day,
        "decisionTimeLocal": f"{cutoff} on {(pd.Timestamp(day) - pd.Timedelta(days=1)).strftime('%Y-%m-%d')} (Europe/London)",
        "cutoffUtc": _cutoff_ts(day, cutoff).tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%SZ"),
        "points": int(len(out)),
        "expectedPoints": POINTS_PER_DAY,
        "firstPublish": None, "lastPublish": None, "meanHorizonH": None,
        "expectedEnergyMwh": None, "peakMw": None, "minMw": None,
        "band": error_band(day, cutoff),
    }
    if not out.empty:
        hz = (out["startTime"] - out["publishTime"]).dt.total_seconds() / 3600
        meta.update({
            "firstPublish": out["publishTime"].min().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "lastPublish": out["publishTime"].max().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "meanHorizonH": float(hz.mean()),
            "expectedEnergyMwh": float(out["forecast"].sum() * FORECAST_STEP_H),  # MW x 1h
            "peakMw": float(out["forecast"].max()),
            "minMw": float(out["forecast"].min()),
        })
        for c in ["startTime", "publishTime", "latestPublishTime"]:
            out[c] = _iso(out[c])
    return _records(out), meta