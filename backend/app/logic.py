import pandas as pd
from pathlib import Path

LONDON = "Europe/London"
DATA = Path(__file__).resolve().parent.parent / "data"


def load():
    act = pd.read_csv(DATA / "actuals.csv")
    fc = pd.read_csv(DATA / "forecasts.csv")
    act["startTime"] = pd.to_datetime(act["startTime"], utc=True)
    fc["startTime"] = pd.to_datetime(fc["startTime"], utc=True)
    fc["publishTime"] = pd.to_datetime(fc["publishTime"], utc=True)
    return act, fc


def decision_forecast(fc, day, cutoff="09:00"):
    """Latest forecast per half-hour that was published before the
    decision cutoff on the day before delivery `day` (YYYY-MM-DD)."""
    day_start = pd.Timestamp(day).tz_localize(LONDON)
    day_end = day_start + pd.Timedelta(days=1)
    cutoff_ts = pd.Timestamp(f"{day} {cutoff}").tz_localize(LONDON) - pd.Timedelta(days=1)

    valid = fc[(fc.startTime >= day_start) & (fc.startTime < day_end)
               & (fc.publishTime <= cutoff_ts)]
    latest = valid.sort_values("publishTime").groupby("startTime").last().reset_index()
    return latest.rename(columns={"generation": "forecast"})


def compare(date_from, date_to, cutoff="09:00"):
    act, fc = load()
    parts = [decision_forecast(fc, d.strftime("%Y-%m-%d"), cutoff)
             for d in pd.date_range(date_from, date_to)]
    f = pd.concat(parts, ignore_index=True)
    a = act.rename(columns={"generation": "actual"})
    df = f.merge(a, on="startTime", how="inner")
    df["error"] = df["forecast"] - df["actual"]
    df["horizon_h"] = (df["startTime"] - df["publishTime"]).dt.total_seconds() / 3600
    return df.sort_values("startTime")


def metrics(df):
    abs_err = df["error"].abs()
    return {
        "n": int(len(df)),
        "mae": float(abs_err.mean()),
        "rmse": float((df["error"] ** 2).mean() ** 0.5),
        "bias": float(df["error"].mean()),
        "p90_abs_error": float(abs_err.quantile(0.9)),
        "nmae_pct": float(abs_err.mean() / df["actual"].mean() * 100),
    }