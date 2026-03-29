# 10-Minute Presentation Notes

## 1. Introduction

Today I will present a simplified but functional LLM Monitoring System built in Python.

The goal was to collect public LLM data, normalize it, store it, score models for enterprise use cases, expose the results through an API, and visualize them in a dashboard.

## 2. Main Modules

The project has three main modules:

1. Data collection and normalization
2. Scoring and recommendation
3. Visualization and digest reporting

## 3. Data Collection

I used two public sources:

- Hugging Face Open LLM Leaderboard
- Vellum LLM Leaderboard

Hugging Face mainly provides benchmark intelligence scores and license information.
Vellum mainly provides operational metrics like cost, speed, latency, and context window.

I created separate collectors for each source and an orchestrator that runs them together.

## 4. Storage Design

I used SQLite with SQLAlchemy.

The main tables are:

- collection runs
- sources
- models
- model metrics
- recommendation results

This design lets the system keep collection history, compare runs, detect new models, and generate reports later.

## 5. Normalization

Because the metrics come from different sources and scales, I normalize them to a common 0-100 range.

For example:

- higher is better for intelligence, speed, and context window
- lower is better for price and latency

I also store both raw values and normalized values for traceability.

## 6. Recommendation Engine

The recommendation engine uses a weighted-average formula.

I defined several enterprise profiles:

- coding_dev
- reasoning_analysis
- enterprise_agents
- long_context_rag
- minimum_cost

Each profile uses different weights depending on what matters most.

## 7. Compliance Filtering

I added a commercial-use filter based on model license metadata.

The rule is conservative:

- clearly permissive licenses are allowed
- restrictive or unclear licenses are excluded

## 8. API And Dashboard

The backend is exposed with FastAPI.

Important endpoints include:

- `/collect`
- `/models`
- `/new-models`
- `/profiles`
- `/recommend`
- `/report/markdown`

For visualization, I built a Streamlit dashboard with:

- model tables
- filters
- profile-based ranking
- charts
- new-model display

## 9. Challenges

The main challenges were:

- public data sources having incomplete metrics
- HTML parsing dependencies
- inconsistent model names between sources
- NaN values appearing from parsed tables

I handled these by adding fallback logic, null-safe parsing, and conservative matching.

## 10. Limitations And Improvements

Current limitations:

- conservative model matching
- some missing public metrics
- local scheduler only

Future improvements:

- better cross-source matching
- more sources
- PDF export
- deployment
- stronger automated testing

## 11. Conclusion

This project is a complete MVP that satisfies the challenge with a simple, modular, and explainable architecture.

It demonstrates data collection, normalization, scoring, storage, API design, dashboard visualization, reporting, and scheduling.
