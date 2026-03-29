"""Simple Streamlit dashboard for the LLM Monitoring System.

This dashboard reads directly from SQLite through the service layer.
That keeps the demo simple because you do not need to run both the API and
the dashboard at the same time.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# Streamlit runs this file from the dashboard folder, so we manually add the
# project root to Python's import path. This keeps imports simple elsewhere.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.database import SessionLocal, init_db
from app.services.dashboard_service import DashboardService


st.set_page_config(
    page_title="LLM Monitoring System",
    page_icon=":bar_chart:",
    layout="wide",
)


def load_dashboard_service() -> DashboardService:
    """Create a dashboard service with a database session."""

    init_db()
    db = SessionLocal()
    return DashboardService(db)


dashboard_service = load_dashboard_service()
summary = dashboard_service.get_dashboard_summary()

st.title("LLM Monitoring System")
st.caption("Simple dashboard for collected LLM benchmark and operational metrics.")

if summary["latest_run_id"] is None:
    st.warning(
        "No completed collection run found yet. Run `python run_collection.py` "
        "or call `POST /collect` from the API first."
    )
    st.stop()

st.subheader("Overview")

metric_column_1, metric_column_2, metric_column_3, metric_column_4 = st.columns(4)
metric_column_1.metric("Latest Run ID", summary["latest_run_id"])
metric_column_2.metric("Total Models", summary["total_models"])
metric_column_3.metric("New Models", summary["new_models_count"])
metric_column_4.metric("Sources", summary["source_count"])

st.sidebar.header("Filters")
available_profiles = dashboard_service.get_profile_options()
available_sources = ["All"] + summary["sources"]
available_licenses = ["All"] + dashboard_service.get_license_types()

selected_profile = st.sidebar.selectbox(
    "Enterprise Profile",
    options=available_profiles,
    index=0,
)
selected_source = st.sidebar.selectbox("Source", options=available_sources, index=0)
selected_license = st.sidebar.selectbox(
    "License",
    options=available_licenses,
    index=0,
)
new_only = st.sidebar.checkbox("New models only", value=False)
commercial_use = st.sidebar.checkbox("Commercial use only", value=False)

source_filter = None if selected_source == "All" else selected_source
license_filter = None if selected_license == "All" else selected_license

models_df = dashboard_service.get_models_dataframe(
    source_name=source_filter,
    license_type=license_filter,
    new_only=new_only,
    selected_profile=selected_profile,
    commercial_use=commercial_use,
)

if models_df.empty:
    st.warning("No models matched the current filters.")
    st.stop()

score_column = f"{selected_profile}_score"

display_columns = [
    "model_name",
    "license_type",
    "source_names",
    "intelligence_score_raw",
    "input_price_per_1m_tokens_raw",
    "output_price_per_1m_tokens_raw",
    "tokens_per_second_raw",
    "ttft_seconds_raw",
    "context_window_raw",
]
if score_column in models_df.columns:
    display_columns.append(score_column)

st.subheader("Collected Models")
st.dataframe(
    models_df[display_columns],
    use_container_width=True,
    hide_index=True,
)

st.subheader(f"Top 5 Models For {selected_profile}")
top_recommendations = dashboard_service.get_top_models_for_profile(
    profile_name=selected_profile,
    top_n=5,
    commercial_use=commercial_use,
)

if top_recommendations:
    top_df = pd.DataFrame(top_recommendations)
    st.dataframe(
        top_df[["rank", "model_name", "profile_score", "license_type", "justification"]],
        use_container_width=True,
        hide_index=True,
    )

    st.bar_chart(
        top_df.set_index("model_name")["profile_score"],
        use_container_width=True,
    )
else:
    st.info("No recommendations are available for the selected profile.")

st.subheader("Model Comparison")
compare_options = models_df["model_name"].tolist()
default_compare = compare_options[: min(3, len(compare_options))]
selected_models = st.multiselect(
    "Select models to compare",
    options=compare_options,
    default=default_compare,
)

if selected_models:
    comparison_df = models_df[models_df["model_name"].isin(selected_models)].copy()
    comparison_columns = [
        "model_name",
        "intelligence_score_raw",
        "input_price_per_1m_tokens_raw",
        "output_price_per_1m_tokens_raw",
        "tokens_per_second_raw",
        "ttft_seconds_raw",
        "context_window_raw",
        score_column,
    ]
    comparison_columns = [
        column_name
        for column_name in comparison_columns
        if column_name in comparison_df.columns
    ]

    st.dataframe(
        comparison_df[comparison_columns],
        use_container_width=True,
        hide_index=True,
    )

st.subheader("Scatter Charts")

scatter_column_1, scatter_column_2 = st.columns(2)

with scatter_column_1:
    if {
        "intelligence_score_raw",
        "input_price_per_1m_tokens_raw",
    }.issubset(models_df.columns):
        scatter_df = models_df[
            [
                "model_name",
                "intelligence_score_raw",
                "input_price_per_1m_tokens_raw",
            ]
        ].dropna()
        if not scatter_df.empty:
            st.caption("Intelligence vs input cost")
            st.scatter_chart(
                scatter_df,
                x="input_price_per_1m_tokens_raw",
                y="intelligence_score_raw",
                size=None,
                color=None,
                use_container_width=True,
            )
        else:
            st.info("Not enough cost data for the intelligence vs cost chart.")

with scatter_column_2:
    if {"tokens_per_second_raw", "ttft_seconds_raw"}.issubset(models_df.columns):
        speed_df = models_df[
            ["model_name", "tokens_per_second_raw", "ttft_seconds_raw"]
        ].dropna()
        if not speed_df.empty:
            st.caption("Speed vs latency")
            st.scatter_chart(
                speed_df,
                x="ttft_seconds_raw",
                y="tokens_per_second_raw",
                size=None,
                color=None,
                use_container_width=True,
            )
        else:
            st.info("Not enough speed and latency data for the scatter chart.")

st.subheader("Newly Detected Models")
new_models = dashboard_service.get_new_models()
if new_models:
    st.write(new_models)
else:
    st.info("No new models detected for the latest run.")
