import re
from datetime import date
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from . import logic

app = FastAPI(title="Wind Forecast Monitor")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

MIN_DAY = date.fromisoformat(logic.MIN_DAY)
MAX_DAY = date.fromisoformat(logic.MAX_DAY)


def validate(date_from: str, date_to: str, cutoff: str):
    try:
        d1, d2 = date.fromisoformat(date_from), date.fromisoformat(date_to)
    except ValueError:
        raise HTTPException(400, "Dates must be in YYYY-MM-DD format.")
    if d1 > d2:
        raise HTTPException(400, "'from' must not be after 'to'.")
    if d1 < MIN_DAY or d2 > MAX_DAY:
        raise HTTPException(
            400, f"Delivery days must be between {MIN_DAY} and {MAX_DAY} "
                 "(decisions made in January 2026).")
    if not re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", cutoff):
        raise HTTPException(400, "cutoff must be HH:MM, e.g. 09:00.")


@app.get("/")
def root():
    return {"status": "ok", "docs": "/docs",
            "deliveryDays": [str(MIN_DAY), str(MAX_DAY)]}


@app.get("/api/decision")
def decision(day: str, cutoff: str = "09:00"):
    validate(day, day, cutoff)
    rows, meta = logic.decision(day, cutoff)
    return {"meta": meta, "rows": rows}


@app.get("/api/compare")
def compare(date_from: str = Query(alias="from"), date_to: str = Query(alias="to"),
            cutoff: str = "09:00"):
    validate(date_from, date_to, cutoff)
    df = logic.compare(date_from, date_to, cutoff)
    if df.empty:
        return []
    out = df[["startTime", "publishTime", "forecast", "actual", "error"]].copy()
    out["startTime"] = logic._iso(out["startTime"])
    out["publishTime"] = logic._iso(out["publishTime"])
    return logic._records(out)


@app.get("/api/metrics")
def metrics(date_from: str = Query(alias="from"), date_to: str = Query(alias="to"),
            cutoff: str = "09:00"):
    validate(date_from, date_to, cutoff)
    return logic.metrics(logic.compare(date_from, date_to, cutoff))


@app.get("/api/metrics/by-hour")
def by_hour(date_from: str = Query(alias="from"), date_to: str = Query(alias="to"),
            cutoff: str = "09:00"):
    validate(date_from, date_to, cutoff)
    return logic.by_hour(logic.compare(date_from, date_to, cutoff))


@app.get("/api/metrics/by-horizon")
def by_horizon(date_from: str = Query(alias="from"), date_to: str = Query(alias="to"),
               cutoff: str = "09:00"):
    validate(date_from, date_to, cutoff)
    return logic.by_horizon(logic.compare(date_from, date_to, cutoff))


@app.get("/api/metrics/by-day")
def by_day(date_from: str = Query(alias="from"), date_to: str = Query(alias="to"),
           cutoff: str = "09:00"):
    validate(date_from, date_to, cutoff)
    return logic.by_day(logic.compare(date_from, date_to, cutoff))