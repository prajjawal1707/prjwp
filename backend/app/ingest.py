import requests
import pandas as pd
from pathlib import Path

BASE = "https://data.elexon.co.uk/bmrs/api/v1/datasets"
DATA = Path(__file__).resolve().parent.parent / "data"


def get(url, params):
    r = requests.get(url, params=params, timeout=120)
    r.raise_for_status()
    return r.json()


def ingest_actuals():
    rows = []
    for start in pd.date_range("2026-01-01", "2026-01-31", freq="7D"):
        end = min(start + pd.Timedelta(days=6), pd.Timestamp("2026-01-31"))
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
    # forecasts for 1 Jan are published from 31 Dec; for 31 Jan, until 30 Jan
    for start in pd.date_range("2025-12-30", "2026-01-31", freq="2D"):
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