# Setup & Reproduction Guide

This file contains the reproduction instructions.

## 1) Create environment
Create new env and run:
```bash
pip install -r requirements.txt
```

## 2) Run the app

```bash
uvicorn app.main:app --reload
```

Open:

- Dashboard: `http://127.0.0.1:8000/dashboard`
- API docs: `http://127.0.0.1:8000/docs`

## 3) First usage

1. Click **Ingest Latest Snapshot** in dashboard.
2. Review KPI cards and chart.
3. Start/stop scheduler with selected interval (minutes).

## 4) Tests and lint

```bash
ruff check .
pytest
```

## 5) Important files

- App entrypoint: `app/main.py`
- API routes: `app/api/routes.py`
- Models: `app/models/station.py`, `app/models/measurement.py`
- Services: `app/services/ingestion.py`, `app/services/analytics.py`, `app/services/scheduler.py`
- UI: `app/templates/dashboard.html`, `app/static/css/dashboard.css`, `app/static/js/dashboard.js`
- ERD: `docs/ERD.md`
- Automation flowchart: `docs/AUTOMATION_FLOW.md`
- CI: `.github/workflows/ci.yml`
- SQLite DB: `data/weather.sqlite`

## 6) Endpoint configuration

By default, ingestion uses:

- `https://data.buienradar.nl/2.0/feed/json`
