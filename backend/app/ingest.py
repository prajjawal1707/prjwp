import requests
import pandas as pd
from pathlib import Path

BASE = "https://data.elexon.co.uk/bmrs/api/v1/datasets"
DATA = Path(__file__).resolve().parent.parent / "data"

# Decisions made 1-31 Jan 2026 (on D-1) are for delivery days 2 Jan - 1 Feb 2026.
# Actuals: a little margin either side. Forecasts: published from late Dec until 1 Feb.
ACT_FROM, ACT_TO = "2026-01-01", "2026-02-01"
FC_FROM, FC_TO = "2025-12-29", "2026-02-02"


def get(url, params):
    r = requests.get(url, params=params, timeout=120)
    r.raise_for_status()
    return r.json()


def ingest_actuals():
    rows = []
    for start in pd.date_range(ACT_FROM, ACT_TO, freq="7D"):
        end = min(start + pd.Timedelta(days=6), pd.Timestamp(ACT_TO))
        rows += get(f"{BASE}/FUELHH/stream", {
            "settlementDateFrom": start.strftime("%Y-%m-%d"),
            "settlementDateTo": end.strftime("%Y-%m-%d"),
            "fuelType": "WIND",
        })
    df = pd.DataFrame(rows)[["startTime", "generation"]].drop_duplicates("startTime")
    df.to_csv(DATA / "actuals.csv", index=False)
    print("actuals:", len(df))


def ingest_forecasts():
    rows = []
    for start in pd.date_range(FC_FROM, FC_TO, freq="2D"):
        end = start + pd.Timedelta(days=2)
        rows += get(f"{BASE}/WINDFOR/stream", {
            "publishDateTimeFrom": start.strftime("%Y-%m-%dT%H:%MZ"),
            "publishDateTimeTo": end.strftime("%Y-%m-%dT%H:%MZ"),
        })
    df = pd.DataFrame(rows)[["startTime", "publishTime", "generation"]]
    df = df.drop_duplicates(["startTime", "publishTime"])
    df.to_csv(DATA / "forecasts.csv", index=False)
    print("forecasts:", len(df))


if __name__ == "__main__":
    DATA.mkdir(exist_ok=True)
    ingest_actuals()
    ingest_forecasts()