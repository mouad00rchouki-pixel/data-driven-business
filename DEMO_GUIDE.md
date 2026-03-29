# Demo Guide

## Deliverable L1: GitHub Repository

Before sharing the repository:

1. Make sure the repo contains:
   - source code
   - `README.md`
   - `TECHNICAL_REPORT.md`
   - generated screenshots if you want
2. Make sure the recruiter can access the repository.
3. If needed, add a short description in the GitHub repo:

`Beginner-friendly LLM Monitoring System built with Python, FastAPI, SQLite, and Streamlit.`

## Deliverable L2: Technical Report (PDF, 3-5 pages)

Use [TECHNICAL_REPORT.md](/Users/mouadrchouki/Documents/Playground/llm_monitoring_system/TECHNICAL_REPORT.md) as your source document.

Recommended PDF structure:

1. Title page
2. Project objective
3. Architecture
4. Technical choices and justification
5. Data sources and schema
6. Challenges encountered
7. Limitations and improvements
8. Screenshots
9. Conclusion

Fastest way to create the PDF:

1. Open `TECHNICAL_REPORT.md`
2. Copy it into Google Docs, Word, or Notion
3. Add screenshots
4. Export as PDF

## Deliverable L3: Functional Demo

If you do not deploy publicly, record a 3-5 minute demo.

### Recommended demo flow

1. Show the repository and README
2. Run one collection:
   - `python run_collection.py`
3. Open Swagger UI:
   - `http://127.0.0.1:8000/docs`
4. Show:
   - `GET /health`
   - `GET /models`
   - `GET /new-models`
   - `GET /profiles`
   - `GET /recommend`
   - `GET /report/markdown`
5. Open the Streamlit dashboard
6. Show:
   - metrics overview
   - filters
   - model table
   - top recommendations
   - charts
7. Mention the scheduler:
   - `python scheduler.py --interval-minutes 10 --max-models-per-source 25`

### What the demo must prove

- Module 1: collection and normalization
- Module 2: scoring and recommendation
- Module 3: visualization and reporting

## Deliverable L4: Oral Presentation

You need a 10-minute presentation plus Q&A.

Use this structure:

1. Problem and objective
2. Architecture overview
3. Data sources
4. Database design
5. Normalization and scoring logic
6. API demo
7. Dashboard demo
8. Limitations and future improvements

## Short Answer Bank

### Why SQLite?

`I used SQLite because it requires zero infrastructure, is easy to run locally, and is enough for an MVP technical challenge.`

### Why FastAPI?

`FastAPI gave me quick development, validation, and built-in Swagger documentation, which made the project easy to test and demo.`

### Why Streamlit?

`Streamlit let me build a usable dashboard very quickly without frontend development.`

### Why weighted scoring?

`Weighted scoring is transparent and easy to explain. It also lets different enterprise profiles emphasize different metrics.`

### Why not fill missing values?

`Because missing data is not the same as bad data. I stored nulls and skipped unavailable metrics during scoring.`
