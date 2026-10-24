import requests, pandas as pd, numpy as np

ELX = "https://data.elexon.co.uk/bmrs/api/v1/datasets"
LIVE = "https://prjwp.onrender.com"      # no trailing slash
CUTOFF_H = 9
DAYS = ["2026-01-02", "2026-01-15", "2026-01-28", "2026-02-01"]


def tget(url, params):
    r = requests.get(url, params=params, timeout=180)
    r.raise_for_status()
    return r.json()


def expected_from_elexon(day):
    """Rebuild the answer from raw Elexon data, without using any app code."""
    d = pd.Timestamp(day, tz="UTC")                 # London == UTC in January
    cutoff = d - pd.Timedelta(days=1) + pd.Timedelta(hours=CUTOFF_H)
    fc = pd.DataFrame(tget(f"{ELX}/WINDFOR/stream", {
        "publishDateTimeFrom": (cutoff - pd.Timedelta(days=3)).strftime("%Y-%m-%dT%H:%MZ"),
        "publishDateTimeTo": cutoff.strftime("%Y-%m-%dT%H:%MZ")}))
    fc["startTime"] = pd.to_datetime(fc["startTime"], utc=True)
    fc["publishTime"] = pd.to_datetime(fc["publishTime"], utc=True)
    fc = fc[(fc.startTime >= d) & (fc.startTime < d + pd.Timedelta(days=1))
            & (fc.publishTime <= cutoff)]
    fc = fc.sort_values("publishTime").groupby("startTime").last().reset_index()

    act = pd.DataFrame(tget(f"{ELX}/FUELHH/stream", {
        "settlementDateFrom": day, "settlementDateTo": day, "fuelType": "WIND"}))
    act = act[act["fuelType"] == "WIND"]
    act["startTime"] = pd.to_datetime(act["startTime"], utc=True)
    return fc.merge(act[["startTime", "generation"]], on="startTime",
                    suffixes=("_fc", "_act"))


print("=== 1. App vs raw Elexon, per sample day ===")
for day in DAYS:
    exp = expected_from_elexon(day)
    live = pd.DataFrame(tget(f"{LIVE}/api/compare",
                             {"from": day, "to": day, "cutoff": "09:00"}))
    live["startTime"] = pd.to_datetime(live["startTime"], utc=True)
    live["publishTime"] = pd.to_datetime(live["publishTime"], utc=True)
    m = exp.merge(live, on="startTime", how="outer", indicator=True)
    ok_rows = (m["_merge"] == "both").all() and len(exp) == len(live) == 24
    ok_fc = np.allclose(m["generation_fc"], m["forecast"])
    ok_act = np.allclose(m["generation_act"], m["actual"])
    ok_pub = (m["publishTime_x"] == m["publishTime_y"]).all()
    print(day, "rows24:", ok_rows, "| forecast:", ok_fc, "| actual:", ok_act,
          "| publishTime:", ok_pub, "->", "PASS" if all([ok_rows, ok_fc, ok_act, ok_pub]) else "FAIL")

print("\n=== 2. Metrics recomputed vs /api/metrics (2 Jan - 1 Feb) ===")
cmp = pd.DataFrame(tget(f"{LIVE}/api/compare",
                        {"from": "2026-01-02", "to": "2026-02-01", "cutoff": "09:00"}))
api = tget(f"{LIVE}/api/metrics", {"from": "2026-01-02", "to": "2026-02-01", "cutoff": "09:00"})
e = cmp["forecast"] - cmp["actual"]
mine = {"n": len(e), "mae": e.abs().mean(), "rmse": float(np.sqrt((e**2).mean())),
        "bias": e.mean(), "p90_abs_error": e.abs().quantile(0.9),
        "nmae_pct": e.abs().mean() / cmp["actual"].mean() * 100}
for k, v in mine.items():
    print(f"{k:14} recomputed={v:12.2f} api={api[k]:12.2f}",
          "PASS" if abs(v - api[k]) < 0.01 else "FAIL")

print("\n=== 3. Cutoff is respected for other cutoffs ===")
for c in ["06:00", "09:00", "12:00"]:
    x = pd.DataFrame(tget(f"{LIVE}/api/compare",
                          {"from": "2026-01-15", "to": "2026-01-15", "cutoff": c}))
    latest = pd.to_datetime(x["publishTime"], utc=True).max()
    limit = pd.Timestamp(f"2026-01-14 {c}", tz="UTC")
    print(c, "latest publish used:", latest, "->", "PASS" if latest <= limit else "FAIL")

print("\n=== 4. Bad input is rejected cleanly ===")
for params in [{"from": "2025-01-01", "to": "2025-01-02"},
               {"from": "2026-01-10", "to": "2026-01-05"},
               {"from": "abc", "to": "2026-01-05"}]:
    r = requests.get(f"{LIVE}/api/metrics", params={**params, "cutoff": "09:00"}, timeout=120)
    print(params, "->", r.status_code, "PASS" if r.status_code == 400 else "FAIL")