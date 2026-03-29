# LLM Monitoring System

This project is a simple and beginner-friendly Python application that collects public LLM benchmark data, stores it in SQLite, scores models for different enterprise profiles, exposes an API with FastAPI, and visualizes results with Streamlit.

The project is designed for a technical challenge, so the code favors:

- readability
- modular structure
- practical error handling
- easy local setup
- interview-friendly explanations

## Project Goals

The application is split into 3 modules:

1. Data collection and normalization
2. Scoring and recommendation engine
3. Visualization and digest report generation

## Tech Stack

- Python 3.11+
- FastAPI
- SQLite
- SQLAlchemy
- pandas
- requests
- BeautifulSoup
- Streamlit
- Pydantic
- Uvicorn

## Why SQLite?

SQLite is a good choice for this challenge because:

- it requires no separate database server
- it stores everything in one local file
- it is simple to explain in an interview
- it is enough for a local demo and MVP

## Project Structure

```text
llm_monitoring_system/
├── app/
│   ├── api/
│   ├── collectors/
│   ├── services/
│   ├── utils/
│   ├── config.py
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   └── schemas.py
├── dashboard/
│   └── streamlit_app.py
├── data/
│   └── llm_monitor.db
├── reports/
├── tests/
├── requirements.txt
├── README.md
└── run_collection.py
```

## Setup

### macOS or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run The API

```bash
uvicorn app.main:app --reload
```

Then open:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Run Data Collection

To collect data and store it in SQLite:

```bash
python run_collection.py
```

## Run The Dashboard

```bash
streamlit run dashboard/streamlit_app.py
```

If the browser does not open automatically, open `http://localhost:8501` manually.

## Generate The Markdown Report

You can generate the report in two ways:

### Option 1: From the script

```bash
python generate_report.py
```

### Option 2: From the API

Open:

```text
http://127.0.0.1:8000/report/markdown
```

Generated reports are saved in the `reports/` folder.

## Optional Simple Scheduler

If you want the project to rerun collection automatically on a fixed interval,
you can use the simple script-based scheduler:

```bash
python scheduler.py --interval-minutes 60 --max-models-per-source 25
```

Example for a quick demo run every 10 minutes:

```bash
python scheduler.py --interval-minutes 10 --max-models-per-source 25
```

Stop it with `Ctrl + C`.

Why this scheduler is reasonable:

- no extra package is required
- easy to explain
- enough for a local MVP demo
- can be replaced later by APScheduler or cron if needed

## Current Status

This repository currently includes:

- dependency list
- project structure
- configuration
- SQLite database setup
- SQLAlchemy models
- Pydantic schemas
- public data collectors
- normalization utilities
- scoring and recommendation logic
- FastAPI endpoints
- Streamlit dashboard
- markdown digest report generation
- simple scheduler

## Main API Endpoints

- `GET /health`
- `POST /collect`
- `GET /models`
- `GET /new-models`
- `GET /profiles`
- `GET /recommend?profile=coding_dev&commercial_use=true`
- `GET /report/markdown`

## Simple Demo Flow

If you need to demo the project quickly, use this order:

1. Run one collection:

```bash
python run_collection.py
```

2. Start the API:

```bash
uvicorn app.main:app --reload
```

3. Open Swagger UI:

```text
http://127.0.0.1:8000/docs
```

4. Test these endpoints in order:

- `GET /health`
- `GET /models`
- `GET /new-models`
- `GET /profiles`
- `GET /recommend`
- `GET /report/markdown`

5. Start the dashboard:

```bash
streamlit run dashboard/streamlit_app.py
```

6. Show:

- overview metrics
- model table
- profile filter
- top 5 recommendations
- charts
- newly detected models

## Architecture Summary

The project is split into clear layers:

- `collectors/`: fetch public data from Hugging Face and Vellum
- `services/`: business logic for collection, recommendation, and dashboard preparation
- `utils/`: normalization, scoring, license filtering, and report generation
- `api/`: FastAPI routes
- `dashboard/`: Streamlit user interface
- `data/`: SQLite database file
- `reports/`: generated markdown digest reports

## Why These Choices Are Reasonable

### Why SQLite?

- zero setup
- one local file
- easy to demo
- enough for an MVP

### Why FastAPI?

- fast to build
- automatic validation
- built-in Swagger docs
- very clean for interview demos

### Why Streamlit?

- fastest way to build a usable dashboard
- no frontend framework needed
- simple charts and filters with little code

### Why a weighted scoring formula?

- easy to explain
- transparent
- profile weights can be adjusted quickly
- better for an oral defense than a black-box ranking method

## Important Design Decisions

- Missing metrics are stored as `NULL` and never fabricated.
- Raw values and normalized values are both stored.
- Missing values are skipped during scoring instead of treated as zero.
- Commercial filtering is conservative: unclear or restrictive licenses are excluded.
- New model detection compares the latest run against the previous completed run.

## Current Limitations

- Cross-source model matching is conservative and based on normalized names.
- Some sources do not expose every metric for every model.
- The first run marks all models as new because there is no earlier baseline.
- Vellum contributes performance and cost metrics, while Hugging Face contributes benchmark and license data, so some rows remain source-specific.

## Interview Talking Points

You can explain the project like this:

- “I built a simple LLM monitoring MVP with real public data, SQLite storage, a scoring engine, an API, and a dashboard.”
- “I optimized for correctness, demo readiness, and explainability rather than over-engineering.”
- “I separated raw collection, normalization, scoring, API access, and visualization into different modules.”
- “I used a weighted-average scoring system because it is transparent and easy to tune for different enterprise profiles.”
- “I never fabricated missing metrics. I stored nulls and designed the scorer to handle incomplete data safely.”

## Submission Checklist

- [ ] Python environment uses 3.11+
- [ ] `pip install -r requirements.txt` completed successfully
- [ ] `python run_collection.py` works
- [ ] SQLite database file exists in `data/`
- [ ] `uvicorn app.main:app --reload` works
- [ ] Swagger UI opens
- [ ] `GET /models` returns data
- [ ] `GET /recommend` returns top 3 results
- [ ] `GET /report/markdown` works
- [ ] `streamlit run dashboard/streamlit_app.py` works
- [ ] Dashboard shows data after collection
- [ ] `python generate_report.py` creates a markdown file in `reports/`

## Suggested Live Demo Script

If the recruiter asks for a walkthrough, use this structure:

1. Explain the challenge goal in one sentence.
2. Show the SQLite-backed architecture and folder structure.
3. Run or show `POST /collect`.
4. Show `/models` and `/new-models`.
5. Show `/recommend` with one profile and the commercial-use filter.
6. Open the Streamlit dashboard and switch profiles.
7. Show the generated markdown report.
8. Mention the scheduler as an optional automation layer.
