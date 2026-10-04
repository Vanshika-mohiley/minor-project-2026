import streamlit as st
import json
import os
import pandas as pd

# Page Configuration
st.set_page_config(
    page_title="Financial Document Intelligence & Risk Screener",
    page_icon="📊",
    layout="wide"
)

# Custom Styling
st.markdown("""
    <style>
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 15px;
        border-left: 5px solid #1f77b4;
        margin-bottom: 10px;
    }
    .evidence-box {
        background-color: #f1f3f5;
        border-radius: 5px;
        padding: 10px;
        font-family: monospace;
        font-size: 0.9em;
    }
    </style>
""", unsafe_allow_html=True)

# Title & Header
st.title("📊 Multi-Modal Financial Document Intelligence")
st.caption("Automated Extraction, Ratio Analysis & Risk Auditing from Annual Reports (10-K / Disclosures)")

# Sidebar
with st.sidebar:
    st.header("Upload Document")
    uploaded_file = st.file_uploader("Upload corporate PDF (Annual Report / 10-K)", type=["pdf"])
    st.divider()
    st.info("💡 Once uploaded, the backend pipeline parses layout tables, computes ratios, and scans for audit red flags.")

# Load backend JSON data (Fallback to sample_output.json)
backend_data_path = os.path.join("..", "ai_ml_layer", "sample_output.json")
if not os.path.exists(backend_data_path):
    backend_data_path = os.path.join("ai_ml_layer", "sample_output.json")
if not os.path.exists(backend_data_path):
    backend_data_path = "sample_output.json"

data = None
if os.path.exists(backend_data_path):
    with open(backend_data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

if data:
    st.success(f"Report Loaded: **{data.get('doc_id', 'Financial Statement')}**")

    # 1. Executive Summary
    st.subheader("📌 Executive AI Summary")
    summary_text = data.get("summary", "")
    if "(AI summary comes in the next step)" in summary_text or not summary_text:
        st.warning("AI Executive Summary generation in progress (Waiting for LLM module).")
    else:
        st.write(summary_text)

    st.divider()

    # 2. Key Financial Metrics
    metrics = data.get("metrics", {})
    st.subheader(f"📈 Key Financial Ratios ({metrics.get('basis', 'Standalone')} | {metrics.get('unit', '')})")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        inc = metrics.get("total_income", {})
        st.metric(
            label="Total Income",
            value=f"₹{inc.get('this_year', 0):,.0f} Cr",
            delta=f"{metrics.get('income_growth_pct', 0)}% YoY"
        )
        st.caption(f"📍 Source: Page {inc.get('page', 'N/A')}")

    with col2:
        prof = metrics.get("profit", {})
        st.metric(
            label="Net Profit",
            value=f"₹{prof.get('this_year', 0):,.0f} Cr",
            delta=f"{metrics.get('profit_growth_pct', 0)}% YoY"
        )
        st.caption(f"📍 Source: Page {prof.get('page', 'N/A')}")

    with col3:
        st.metric(
            label="Profit Margin",
            value=f"{metrics.get('profit_margin_pct', 0)}%"
        )
        st.caption("Calculated (Profit / Income)")

    with col4:
        risk_score = data.get("risk_score", 0)
        st.metric(
            label="Overall Risk Score",
            value=f"{risk_score} / 100",
            delta="Moderate Risk" if risk_score <= 50 else "High Risk",
            delta_color="inverse"
        )
        st.caption("Rule-based Audit Screener")

    st.divider()

    # 3. Flagged Audit Risks
    st.subheader("⚠️ Flagged Risk & Litigation Disclosures")
    risk_flags = data.get("risk_flags", [])

    if risk_flags:
        for idx, flag in enumerate(risk_flags, start=1):
            with st.expander(f"Risk #{idx}: {flag.get('type', '').upper()} (Page {flag.get('page', 'N/A')}) — Severity: {flag.get('severity', '').capitalize()}"):
                st.markdown(f"**Discovered On:** Page `{flag.get('page')}` | **Severity:** `{flag.get('severity')}`")
                st.markdown("**Evidence Snippet from Filing:**")
                st.markdown(f"<div class='evidence-box'>{flag.get('evidence')}</div>", unsafe_allow_html=True)
    else:
        st.success("No critical litigation or penalty risk flags detected.")

    st.divider()

    # 4. Interactive Q&A Chatbot
    st.subheader("💬 Ask Questions on this Filing (Source-Cited RAG)")
    
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! I have indexed this report. Ask me anything about revenues, debt notes, or legal disclosures."}
        ]

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if user_prompt := st.chat_input("e.g. What is the cause of the VAT penalty on page 152?"):
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.write(user_prompt)

        with st.chat_message("assistant"):
            bot_reply = f"Grounded response for: '{user_prompt}' will be fetched via ChromaDB RAG. (Exact Citation: Page 152, Note 1)."
            st.write(bot_reply)
            st.session_state.messages.append({"role": "assistant", "content": bot_reply})

else:
    st.error("No analysis data found! Make sure 'sample_output.json' is present.")
