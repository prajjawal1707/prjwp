# UK Wind Forecast Monitor

A web app that helps a UK energy utility's day-ahead trading desk answer two questions about national wind generation:

1. **What is the latest wind forecast I actually had when I had to make the purchase decision?**
2. **How accurate has that forecast been, in numbers, so I can size my risk buffer?**

Scope: purchase decisions made in **January 2026** (delivery days **2 Jan - 1 Feb 2026**), using only Elexon BMRS data:
- Actuals: `FUELHH` (filtered to `fuelType = WIND`)
- Forecasts: `WINDFOR`

## Live demo

| Part | Link |
|---|---|
| Web app (React, Vercel) | https://prjwp.vercel.app/ |
| API (FastAPI, Render) | https://prjwp.onrender.com/docs |

> The API runs on Render's free tier and sleeps when idle. The first request after a quiet period can take up to about a minute. Open the API link first to wake it up.
>
> Deployment note: the brief names Vercel or Heroku. The front-end is on Vercel; the back-end container is on Render.

## AI tools used

This project was built with the help of **Claude (by Anthropic)**, an AI assistant. It was used for planning, code generation, debugging and drafting documentation. I reviewed the output, wrote tests, and verified the results independently against Elexon's raw API (see [Verification](#verification)).

## What the app does

**1. Decision view**
- Pick a delivery day. The app shows the latest forecast for each hour that was published **at or before the decision time** (default 09:00 London time on the previous day).
- Summary cards: expected wind energy (MWh), peak and lowest forecast (MW), and a typical-error figure.
- A shaded band shows the likely range (forecast +/- the P90 absolute error from earlier days).
- An optional "hindsight" toggle overlays the newest forecast and the actual output, clearly labelled as not known at decision time.

**2. Forecast accuracy view**
- Pick a date range. Each delivery day is judged on the forecast that was available at the decision time, compared with actual generation.
- KPI cards: MAE, RMSE, bias, P90 absolute error, nMAE %.
- Charts: actual vs forecast, and error by hour of day, by forecast lead time, and by delivery day.

The decision time is adjustable in the page header.

## Key findings (January 2026, 09:00 decision time, n = 744 hourly points)

| Metric | Value |
|---|---|
| MAE | 2,022 MW |
| RMSE | 2,497 MW |
| Bias (forecast - actual) | +1,746 MW (forecast ran high) |
| P90 absolute error | 4,154 MW |
| nMAE | 17.9 % of mean actual output |

The largest errors occurred in the early morning (about 03:00-05:00), and on 28 Jan, 12 Jan and 11 Jan the forecast was too high in every hour.

## Repository layout

```
.
├── README.md
├── docker-compose.yml          Runs front-end + back-end together
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py             FastAPI routes + input validation
│   │   ├── logic.py            Forecast selection, comparison, metrics
│   │   └── ingest.py           Downloads Elexon data into CSV files
│   ├── data/
│   │   ├── actuals.csv         Cached FUELHH wind actuals
│   │   └── forecasts.csv       Cached WINDFOR forecasts
│   ├── tests/
│   │   ├── test_logic.py            Unit tests (synthetic data)
│   │   └── test_data_integrity.py   Checks on the real cached data
│   ├── verify.py               Independent check: live API vs raw Elexon API
│   ├── pytest.ini
│   ├── requirements.txt
│   ├── .dockerignore
│   └── Dockerfile
└── frontend/
    ├── src/
    │   ├── main.jsx
    │   ├── App.jsx             Tabs + shared decision-time control
    │   ├── App.css
    │   ├── api.js              All API calls and error handling
    │   ├── config.js           Date limits and small helpers
    │   └── components/
    │       ├── DecisionView.jsx
    │       ├── AccuracyView.jsx
    │       ├── KpiCards.jsx
    │       └── CompareChart.jsx
    ├── index.html
    ├── package.json
    ├── vite.config.js          Dev proxy: /api -> localhost:8000
    ├── nginx.conf              Serves the build and proxies /api in Docker
    ├── .dockerignore
    └── Dockerfile
```

Small helper scripts used during development (such as `diag.py` and `headline.py`) are not required to run the app.

## How to run

### Option 1: Docker (recommended)

```bash
docker compose up --build
```

- App: http://localhost:3000
- API docs: http://localhost:8000/docs

### Option 2: Run locally

**Back-end** (Python 3.12 recommended)

```bash
cd backend
python -m venv venv
venv\Scripts\activate            # Windows  (macOS/Linux: source venv/bin/activate)
pip install -r requirements.txt
uvicorn app.main:app --reload    # http://localhost:8000/docs
```

The cached data is already in `backend/data/`. To re-download it from Elexon:

```bash
python -m app.ingest
```

**Front-end**

```bash
cd frontend
npm install
npm run dev                      # http://localhost:5173 (proxies /api to :8000)
```

### Tests and verification

```bash
cd backend
pytest -v                        # 11 tests
python verify.py                 # compares the live API with raw Elexon data
```

### Deployment settings

- **Back-end (Render):** Docker service, root directory `backend`. The Dockerfile starts `uvicorn` on `$PORT`.
- **Front-end (Vercel):** root directory `frontend`, Vite preset, environment variable `VITE_API_URL=https://prjwp.onrender.com` (no trailing slash). Vite reads it at build time, so redeploy after changing it.

## API

| Endpoint | Purpose |
|---|---|
| `GET /api/decision?day=YYYY-MM-DD&cutoff=HH:MM` | Forecast available at the decision time for one delivery day, plus summary and error band |
| `GET /api/compare?from=&to=&cutoff=` | Hourly decision-time forecast vs actual and error |
| `GET /api/metrics?from=&to=&cutoff=` | MAE, RMSE, bias, P90, nMAE for a range |
| `GET /api/metrics/by-hour` / `by-horizon` / `by-day` | Same metrics, grouped |

Invalid input (bad format, `from` after `to`, dates outside 2 Jan - 1 Feb 2026, bad cutoff) returns HTTP 400 with a clear message.

## Method and definitions

**Forecast selection rule.** For delivery day D and a decision time T (default 09:00 London time on D-1), for each target hour use the WINDFOR forecast with the **latest `publishTime` that is less than or equal to the decision time**. Forecasts published later are never used.

**Error** = forecast - actual. Positive means the forecast was too high.

| Metric | Meaning |
|---|---|
| MAE | Mean absolute error: the typical size of the miss |
| RMSE | Root mean squared error: penalises large misses more |
| Bias | Mean error: a systematic tendency to over- (+) or under- (-) forecast |
| P90 absolute error | 90 % of misses are smaller than this; useful for sizing a buffer |
| nMAE % | MAE divided by mean actual output |

**Uncertainty band (Decision view).** +/- the P90 absolute error computed only from delivery days up to **D-2**, because actuals for D-1 are not complete at decision time. This avoids look-ahead.

## Assumptions and limitations

1. **Decision time is assumed to be 09:00 London time on D-1** and is adjustable. Real gate closure depends on the exchange and is often around 09:30.
2. **"Decisions made in January 2026"** is interpreted as delivery days 2 Jan - 1 Feb 2026 (decision on D-1). Forecasts published from late Dec onwards are downloaded.
3. **Hourly vs half-hourly.** WINDFOR is published hourly and FUELHH half-hourly. Data is joined on `startTime`, so accuracy is measured on 24 hourly points per day (744 for the month). Nothing is interpolated.
4. **Time zones.** Data is kept in UTC. The decision time is built in `Europe/London`. January has no daylight-saving change, and a unit test covers the summer-time case.
5. **Positive bias.** The forecast ran about 1.7 GW higher than FUELHH actuals. The cause is not established: it could be a genuine forecast bias or a difference in what the two datasets cover. It should be investigated before acting on it.
6. **Lead time and hour of day are linked** under a single fixed cutoff, so the by-lead-time chart should not be read as a pure effect of forecast age. Comparing several cutoffs would separate them.
7. **One month of data.** Results should not be generalised to other seasons.
8. The uncertainty band is symmetric although the error is skewed towards over-forecasting.
9. The data is cached in CSV files and is not refreshed automatically.

## Verification

- **Unit tests** (`tests/test_logic.py`): a forecast published after the cutoff is never selected; one published exactly at the cutoff is included; the latest eligible forecast wins; only target-day rows are returned; the cutoff respects British Summer Time; metrics values are correct.
- **Real-data tests** (`tests/test_data_integrity.py`): 24 points for each of the 31 days; WINDFOR is hourly; no forecast used was published after its cutoff; lead times are positive; an empty range is handled safely.
- **`verify.py`**: rebuilds four sample days directly from Elexon's raw API and checks that the live app returns identical rows, forecast values, actuals and publish times; recomputes all metrics independently; checks the cutoff at 06:00, 09:00 and 12:00; confirms bad input is rejected with HTTP 400.

## Possible next steps

- Asymmetric, bias-aware uncertainty band.
- Multi-cutoff comparison to isolate the effect of forecast age.
- Investigate the cause of the positive bias.
- Break errors down by wind level and weather regime.
- Add demand data to turn the forecast into a buy-volume recommendation.
- Replace CSVs with a database and a scheduled refresh.

## Data source

Elexon Insights Solution (BMRS) API: https://bmrs.elexon.co.uk/api-documentation