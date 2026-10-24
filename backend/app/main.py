from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from . import logic

app = FastAPI(title="Wind Forecast Monitor")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])


@app.get("/api/compare")
def compare(date_from: str = Query(alias="from"), date_to: str = Query(alias="to"),
            cutoff: str = "09:00"):
    df = logic.compare(date_from, date_to, cutoff)
    out = df[["startTime", "publishTime", "forecast", "actual", "error"]].copy()
    out["startTime"] = out["startTime"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    out["publishTime"] = out["publishTime"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    return out.to_dict("records")


@app.get("/api/metrics")
def metrics(date_from: str = Query(alias="from"), date_to: str = Query(alias="to"),
            cutoff: str = "09:00"):
    return logic.metrics(logic.compare(date_from, date_to, cutoff))