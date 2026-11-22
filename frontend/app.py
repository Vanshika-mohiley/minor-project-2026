import hashlib
import html
import json
import os
import sys
import tempfile

import plotly.graph_objects as go
import streamlit as st

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ML_DIR = os.path.join(ROOT, "ai_ml_layer")
CACHE_DIR = os.path.join(ML_DIR, "cache")
SAMPLE_PATH = os.path.join(ML_DIR, "sample_output.json")
sys.path.insert(0, ML_DIR)

st.set_page_config(
    page_title="Financial Document Intelligence & Risk Screener",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
    <style>
    .evidence-box {
        background-color: #f5f5f7;
        color: #1d1d1f;
        border-left: 4px solid #dc3545;
        border-radius: 4px;
        padding: 12px;
        font-family: 'Courier New', Courier, monospace;
        font-size: 0.88em;
        line-height: 1.5;
    }
    .badge-litigation {
        background-color: #ffeeba;
        color: #856404;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 0.8em;
        font-weight: 600;
    }
    .badge-penalty {
        background-color: #f8d7da;
        color: #721c24;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 0.8em;
        font-weight: 600;
    }
    .badge-other {
        background-color: #e9ecef;
        color: #343a40;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 0.8em;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)


def run_analysis(pdf_path, basis):
    from analysis.analyze import analyze
    return analyze(pdf_path, basis=basis)


def get_report(file_bytes, file_name, basis):
    """Return (report_dict, loaded_from_cache). Runs the analysis only if it is not cached."""
    key = hashlib.md5(file_bytes).hexdigest() + "_" + basis
    cache_file = os.path.join(CACHE_DIR, key + ".json")
    if os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f), True

    folder = tempfile.mkdtemp()
    pdf_path = os.path.join(folder, os.path.basename(file_name))
    with open(pdf_path, "wb") as f:
        f.write(file_bytes)

    with st.spinner("Analysing the report. A long report takes about 4-5 minutes, please do not refresh the page..."):
        report = run_analysis(pdf_path, basis)

    result = report.model_dump()
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False)
    return result, False


def money(value):
    if value is None:
        return "n/a"
    return f"₹{value:,.0f} Cr"


def signed(value, suffix):
    if value is None:
        return None
    return f"{value:+.1f}{suffix}"


def ratio(top, bottom):
    if top is None or not bottom:
        return None
    return top / bottom * 100


def source_text(page):
    if page is None:
        return "Not found in this report"
    return f"📍 Source: Page {page}"


def difference(now, before):
    if now is None or before is None:
        return None
    return now - before


st.title("📈 Multi-Modal Financial Document Intelligence")
st.caption("AI-powered annual report analysis: key figures, ratios and risk screening")

with st.sidebar:
    st.header("📂 Document Ingestion")
    uploaded_file = st.file_uploader("Upload an annual report (PDF)", type=["pdf"])
    basis = st.selectbox(
        "Figures basis (optional)",
        ["Unspecified", "Standalone", "Consolidated"],
        help="The program cannot detect this yet. Choose it if you know which one the report uses.",
    )
    st.divider()
    st.markdown("### 🛠️ How it works")
    st.markdown("- **Reader:** PyMuPDF (text and tables)")
    st.markdown("- **Figures and ratios:** calculated by Python, not by AI")
    st.markdown("- **Risk judge and summary:** local llama3.2:3b model via Ollama")
    st.markdown("- **Risk score:** rule-based, from 0 to 100")

data = None
if uploaded_file is not None:
    try:
        data, from_cache = get_report(uploaded_file.getvalue(), uploaded_file.name, basis)
        if from_cache:
            st.success("Loaded the saved analysis for this file.")
        else:
            st.success("Analysis finished.")
    except Exception as error:
        st.error(
            "The analysis failed: " + str(error)
            + ". Make sure Ollama is running (ollama serve) and the model is installed (ollama pull llama3.2:3b)."
        )
elif os.path.exists(SAMPLE_PATH):
    with open(SAMPLE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    st.info("Demo mode: showing the saved analysis of the Infosys annual report. Upload a PDF in the sidebar to analyse another report.")

if data:
    st.info("📄 Document: **" + str(data.get("doc_id", "Financial Report")) + "**")

    st.subheader("📌 Executive Summary")
    summary_text = data.get("summary") or ""
    if not summary_text or "(AI summary comes in the next step)" in summary_text:
        st.warning("No AI summary is available in this analysis yet.")
    else:
        st.write(summary_text)

    st.divider()

    metrics = data.get("metrics") or {}
    unit = metrics.get("unit", "INR crore")
    basis_label = metrics.get("basis", "Unspecified")

    def part(name):
        d = metrics.get(name) or {}
        return d.get("this_year"), d.get("last_year"), d.get("page")

    inc_now, inc_before, inc_page = part("total_income")
    prof_now, prof_before, prof_page = part("profit")
    assets_now, assets_before, assets_page = part("total_assets")
    equity_now, equity_before, equity_page = part("total_equity")

    margin_now = metrics.get("profit_margin_pct")
    margin_delta = difference(margin_now, ratio(prof_before, inc_before))
    equity_ratio_now = metrics.get("equity_to_assets_pct")
    equity_ratio_delta = difference(equity_ratio_now, ratio(equity_before, assets_before))

    st.subheader("📊 Financial Performance Overview (" + basis_label + " | " + unit + ")")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Income", money(inc_now), delta=signed(metrics.get("income_growth_pct"), "% YoY"))
        st.caption(source_text(inc_page))
    with col2:
        st.metric("Net Profit", money(prof_now), delta=signed(metrics.get("profit_growth_pct"), "% YoY"))
        st.caption(source_text(prof_page))
    with col3:
        margin_text = "n/a" if margin_now is None else f"{margin_now}%"
        st.metric("Net Profit Margin", margin_text, delta=signed(margin_delta, " pts vs last year"))
        st.caption("Calculated: Net Profit / Total Income")
    with col4:
        equity_text = "n/a" if equity_ratio_now is None else f"{equity_ratio_now}%"
        st.metric("Equity to Assets", equity_text, delta=signed(equity_ratio_delta, " pts vs last year"))
        st.caption("Assets " + source_text(assets_page))

    st.markdown("<br>", unsafe_allow_html=True)

    chart_col, gauge_col = st.columns([3, 2])

    with chart_col:
        labels, before_vals, now_vals = [], [], []
        for name, before, now in [
            ("Total Income", inc_before, inc_now),
            ("Net Profit", prof_before, prof_now),
            ("Total Equity", equity_before, equity_now),
        ]:
            if before is not None and now is not None:
                labels.append(name)
                before_vals.append(before)
                now_vals.append(now)
        if labels:
            fig_bar = go.Figure(data=[
                go.Bar(name="Last Year", x=labels, y=before_vals, marker_color="#90caf9"),
                go.Bar(name="This Year", x=labels, y=now_vals, marker_color="#1976d2"),
            ])
            fig_bar.update_layout(
                title="Year-over-Year Comparison",
                barmode="group",
                height=320,
                margin=dict(l=20, r=20, t=40, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No year-over-year figures could be read from this report.")

    with gauge_col:
        risk_score = data.get("risk_score", 0)
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=risk_score,
            title={"text": "Risk Score (0-100)"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "#0071e3"},
                "steps": [
                    {"range": [0, 35], "color": "#c8e6c9"},
                    {"range": [35, 70], "color": "#fff59d"},
                    {"range": [70, 100], "color": "#ffcdd2"},
                ],
                "threshold": {"line": {"color": "red", "width": 4}, "thickness": 0.75, "value": 70},
            },
        ))
        fig_gauge.update_layout(height=320, margin=dict(l=40, r=40, t=40, b=20))
        st.plotly_chart(fig_gauge, use_container_width=True)
        st.caption("A rough rule-based indicator, not a verdict. Flagged items need a human review.")

    st.divider()

    st.subheader("⚠️ Risk Flags")
    risk_flags = data.get("risk_flags") or []

    if risk_flags:
        for idx, flag in enumerate(risk_flags, start=1):
            flag_type = str(flag.get("type", "general")).lower()
            if "penalty" in flag_type:
                badge_class = "badge-penalty"
            elif "litigation" in flag_type:
                badge_class = "badge-litigation"
            else:
                badge_class = "badge-other"
            severity = str(flag.get("severity", ""))

            with st.expander("Flag #" + str(idx) + " — " + flag_type.upper() + " | Severity: " + severity.capitalize() + " (Page " + str(flag.get("page", "N/A")) + ")"):
                st.markdown(
                    "**Category:** <span class='" + badge_class + "'>" + html.escape(flag_type.upper()) + "</span>"
                    + " &nbsp;|&nbsp; **Severity:** `" + severity + "` &nbsp;|&nbsp; **Page:** `" + str(flag.get("page", "N/A")) + "`",
                    unsafe_allow_html=True,
                )
                st.markdown("**Extracted text evidence:**")
                st.markdown(
                    "<div class='evidence-box'>" + html.escape(str(flag.get("evidence", ""))) + "</div>",
                    unsafe_allow_html=True,
                )
    else:
        st.success("✅ No risk flags were confirmed in this report.")

    st.divider()

    st.subheader("💬 Ask Questions on this Report")
    st.info("Question answering with page citations is coming soon.")

elif uploaded_file is None:
    st.error("No analysis data found. Make sure ai_ml_layer/sample_output.json is present.")
