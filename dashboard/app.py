"""Streamlit dashboard for support ticket triage results."""

from pathlib import Path
import sys
import subprocess

import pandas as pd
import plotly.express as px
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"

st.set_page_config(
    page_title="Support Ticket Triage",
    page_icon=":ticket:",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .main { background: #f7f9fc; }
    .block-container { padding-top: 1.5rem; }
    [data-testid="stMetric"] {
        background: white;
        border: 1px solid #d9e2ef;
        border-radius: 16px;
        min-height: 132px;
        padding: 20px 22px;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.10);
    }
    [data-testid="stMetricLabel"] {
        color: #64748b !important;
        font-size: 16px !important;
        font-weight: 600 !important;
    }
    [data-testid="stMetricValue"] {
        color: #0f172a !important;
        font-size: 40px !important;
        font-weight: 750 !important;
        line-height: 1.15 !important;
        padding-top: 8px;
    }
    [data-testid="stMetricDelta"] {
        color: #475569 !important;
    }
    .hero {
        background: linear-gradient(135deg, #1d3557 0%, #457b9d 100%);
        color: white;
        border-radius: 16px;
        padding: 22px 26px;
        margin-bottom: 18px;
    }
    .hero h1, .hero p { color: white; margin: 0; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=10)
def load_outputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    """Load the latest pipeline CSV and JSON outputs."""
    results = pd.read_csv(
        OUTPUTS / "results.csv",
        dtype=str,
        keep_default_na=False,
    )
    details = pd.read_csv(
        OUTPUTS / "details.csv",
        dtype=str,
        keep_default_na=False,
    )
    review = pd.read_csv(
        OUTPUTS / "review_queue.csv",
        dtype=str,
        keep_default_na=False,
    )
    import json

    report = json.loads(
        (OUTPUTS / "run_report.json").read_text(encoding="utf-8")
    )
    return results, details, review, report


def rerun_mock_pipeline() -> None:
    """Rerun the deterministic mock pipeline and refresh dashboard data."""
    completed = subprocess.run(
        [sys.executable, "main.py", "--mock"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        st.error(completed.stderr or completed.stdout or "Mock pipeline failed.")
        return
    load_outputs.clear()
    st.success("Mock pipeline completed.")
    st.rerun()


with st.sidebar:
    st.title("Triage Control")
    page = st.radio(
        "View",
        ["Overview", "Human Review", "Ticket Explorer", "Run Data"],
    )
    st.divider()
    st.caption("Latest pipeline output")
    if st.button("Rerun mock pipeline", use_container_width=True):
        rerun_mock_pipeline()
    st.caption("The mock client uses deterministic keyword logic.")

try:
    results, details, review, report = load_outputs()
except (FileNotFoundError, pd.errors.EmptyDataError, ValueError) as exc:
    st.error(f"Pipeline outputs are unavailable: {exc}")
    st.stop()

st.markdown(
    """
    <div class="hero">
      <h1>Support Ticket Triage</h1>
      <p>Operational view of categories, priorities, latency, and human review.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if page == "Overview":
    total = int(report["total"])
    auto_resolved = int(report["auto_resolved"])
    sent_to_review = int(report["sent_to_review"])

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Total tickets", f"{total:,}")
    kpi2.metric("Auto resolved", f"{auto_resolved:,}")
    kpi3.metric("Sent to review", f"{sent_to_review:,}")
    kpi4.metric("Review rate", f"{float(report['review_rate']):.1%}")

    left, right = st.columns(2)
    with left:
        category_data = report["category_distribution_auto_resolved"]
        category_frame = pd.DataFrame(
            {"Category": list(category_data),
             "Tickets": list(category_data.values())}
        )
        fig = px.bar(
            category_frame,
            x="Tickets",
            y="Category",
            orientation="h",
            title="Auto-resolved categories",
            color="Tickets",
            color_continuous_scale="Blues",
        )
        fig.update_layout(height=360, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    with right:
        priority_data = report["priority_distribution_auto_resolved"]
        priority_frame = pd.DataFrame(
            {"Priority": list(priority_data),
             "Tickets": list(priority_data.values())}
        )
        fig = px.pie(
            priority_frame,
            names="Priority",
            values="Tickets",
            title="Auto-resolved priorities",
            hole=0.58,
        )
        fig.update_traces(textposition="inside", textinfo="percent+label")
        fig.update_layout(height=360)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Why tickets need review")
    reason_data = report["review_reasons_count"]
    reason_frame = pd.DataFrame(
        {"Reason": list(reason_data),
         "Tickets": list(reason_data.values())}
    ).sort_values("Tickets", ascending=False)
    fig = px.bar(
        reason_frame,
        x="Tickets",
        y="Reason",
        orientation="h",
        title="Review reason counts",
        color="Tickets",
        color_continuous_scale="Teal",
    )
    fig.update_layout(height=max(320, 30 * len(reason_frame)), coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)

    a, b, c, d = st.columns(4)
    a.metric("LLM successes", f"{int(report['llm_success_count']):,}")
    b.metric("LLM failures", f"{int(report['llm_failure_count']):,}")
    c.metric("Fallbacks", f"{int(report['fallback_count']):,}")
    d.metric("Cache hits", f"{int(report['cache_hits']):,}")

elif page == "Human Review":
    st.subheader("Human review queue")
    st.caption("Tickets that need a person to confirm category or priority.")

    search = st.text_input("Search subject or customer")
    filtered = review.copy()
    if search:
        needle = search.lower()
        filtered = filtered[
            filtered["subject"].str.lower().str.contains(needle, na=False)
            | filtered["customer"].str.lower().str.contains(needle, na=False)
        ]

    st.download_button(
        "Download review queue",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="review_queue.csv",
        mime="text/csv",
    )
    st.dataframe(
        filtered,
        use_container_width=True,
        hide_index=True,
        height=520,
    )

elif page == "Ticket Explorer":
    st.subheader("Ticket explorer")

    category_options = sorted(
        set(results["category"].dropna()) - {""}
    )
    priority_options = sorted(
        set(results["priority"].dropna()) - {""}
    )
    categories = st.multiselect("Category", category_options)
    priorities = st.multiselect("Priority", priority_options)
    review_state = st.pills(
        "Review state",
        ["all", "yes", "no"],
        default="all",
    )
    search = st.text_input("Search ticket ID")

    filtered = results.copy()
    if categories:
        filtered = filtered[filtered["category"].isin(categories)]
    if priorities:
        filtered = filtered[filtered["priority"].isin(priorities)]
    if review_state != "all":
        filtered = filtered[filtered["needs_review"] == review_state]
    if search:
        filtered = filtered[
            filtered["id"].str.lower().str.contains(search.lower(), na=False)
        ]

    st.caption(f"{len(filtered)} of {len(results)} tickets")
    st.dataframe(
        filtered,
        use_container_width=True,
        hide_index=True,
        height=520,
    )

else:
    st.subheader("Run diagnostics")

    diag1, diag2, diag3 = st.columns(3)
    diag1.metric("Average latency", f"{float(report['avg_latency_ms']):.2f} ms")
    diag2.metric("P95 latency", f"{float(report['p95_latency_ms']):.2f} ms")
    diag3.metric("Estimated tokens", f"{int(report['total_estimated_tokens']):,}")

    c1, c2 = st.columns(2)
    c1.metric("Retries", f"{int(report['retries']):,}")
    c2.metric("Cache hits", f"{int(report['cache_hits']):,}")

    st.subheader("Decision details")
    st.dataframe(details, use_container_width=True, hide_index=True, height=520)
