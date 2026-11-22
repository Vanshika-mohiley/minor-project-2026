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
    page_title="FinSight AI | Document Intelligence & Risk Screener",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Premium Executive Styling
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Hero Banner */
    .hero-banner {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 60%, #0f4c81 100%);
        padding: 28px 32px;
        border-radius: 16px;
        color: #ffffff;
        margin-bottom: 24px;
        box-shadow: 0 10px 25px rgba(15, 23, 42, 0.15);
        border: 1px solid rgba(255, 255, 255, 0.08);
    }
    .hero-title {
        font-size: 1.85rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.02em;
    }
    .hero-subtitle {
        color: #94a3b8;
        font-size: 0.95rem;
        margin-top: 6px;
        margin-bottom: 0;
    }
    .hero-pill {
        display: inline-block;
        background: rgba(56, 189, 248, 0.15);
        color: #38bdf8;
        border: 1px solid rgba(56, 189, 248, 0.3);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
        margin-bottom: 10px;
    }

    /* Executive Summary Card */
    .summary-card {
        background: linear-gradient(to right, #f8fafc, #ffffff);
        border: 1px solid #e2e8f0;
        border-left: 5px solid #2563eb;
        border-radius: 12px;
        padding: 20px 24px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
        color: #1e293b;
        line-height: 1.65;
        font-size: 0.96rem;
    }

    /* Custom KPI Card */
    .kpi-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 18px 20px;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.02);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(37, 99, 235, 0.08);
        border-color: #bfdbfe;
    }
    .kpi-label {
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: #64748b;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-size: 1.65rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 6px;
    }
    .kpi-delta-pos {
        display: inline-block;
        background: #dcfce7;
        color: #166534;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.78rem;
        font-weight: 600;
    }
    .kpi-delta-neg {
        display: inline-block;
        background: #fee2e2;
        color: #991b1b;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.78rem;
        font-weight: 600;
    }
    .kpi-delta-neutral {
        display: inline-block;
        background: #f1f5f9;
        color: #475569;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.78rem;
        font-weight: 600;
    }
    .kpi-source {
        font-size: 0.75rem;
        color: #94a3b8;
        margin-top: 8px;
    }

    /* Evidence Box */
    .evidence-box {
        background-color: #0f172a;
        color: #e2e8f0;
        border-left: 4px solid #f43f5e;
        border-radius: 8px;
        padding: 14px 16px;
        font-family: 'Courier New', Courier, monospace;
        font-size: 0.86em;
        line-height: 1.55;
        margin-top: 8px;
    }

    /* Badges */
    .badge-high {
        background-color: #fee2e2;
        color: #991b1b;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.76em;
        font-weight: 700;
    }
    .badge-medium {
        background-color: #fef3c7;
        color: #92400e;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.76em;
        font-weight: 700;
    }
    .badge-type {
        background-color: #e0e7ff;
        color: #1e40af;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.76em;
        font-weight: 700;
    }
    </style>
""", unsafe_allow_html=True)


def run_analysis(pdf_path, basis):
    from analysis.analyze import analyze
    return analyze(pdf_path, basis=basis)


def get_report(file_bytes, file_name, basis):
    key = hashlib.md5(file_bytes).hexdigest() + "_" + basis
    cache_file = os.path.join(CACHE_DIR, key + ".json")
    if os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f), True

    folder = tempfile.mkdtemp()
    pdf_path = os.path.join(folder, os.path.basename(file_name))
    with open(pdf_path, "wb") as f:
        f.write(file_bytes)

    with st.status("Running Multi-Stage Financial Intelligence Pipeline...", expanded=True) as status:
        st.write("📄 Extracting text & financial tables via PyMuPDF...")
        st.write("🧮 Computing YoY ratios & balance sheet metrics...")
        st.write("🛡️ Screening legal disclosures via Llama-3.2 Judge...")
        report = run_analysis(pdf_path, basis)
        status.update(label="Analysis Complete!", state="complete", expanded=False)

    result = report.model_dump()
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False)
    return result, False


def money(value):
    if value is None:
        return "N/A"
    return f"₹{value:,.0f} Cr"


def ratio(top, bottom):
    if top is None or not bottom:
        return None
    return top / bottom * 100


def difference(now, before):
    if now is None or before is None:
        return None
    return now - before


def render_kpi_card(label, value_str, delta_val, delta_suffix, source_str):
    if delta_val is None:
        delta_html = "<span class='kpi-delta-neutral'>Baseline Metric</span>"
    elif delta_val > 0:
        delta_html = f"<span class='kpi-delta-pos'>▲ +{delta_val:.1f}{delta_suffix}</span>"
    elif delta_val < 0:
        delta_html = f"<span class='kpi-delta-neg'>▼ {delta_val:.1f}{delta_suffix}</span>"
    else:
        delta_html = f"<span class='kpi-delta-neutral'>0.0{delta_suffix}</span>"

    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value_str}</div>
            <div>{delta_html}</div>
            <div class="kpi-source">{source_str}</div>
        </div>
    """, unsafe_allow_html=True)


def answer_question_from_report(query, data):
    """Grounded Q&A engine answering directly from extracted report data + citations."""
    q = query.lower()
    metrics = data.get("metrics") or {}
    flags = data.get("risk_flags") or []

    if any(w in q for w in ["income", "revenue", "sales", "top line"]):
        inc = metrics.get("total_income") or {}
        return (
            f"**Total Income ({metrics.get('basis', 'Reported')}):** {money(inc.get('this_year'))} "
            f"(vs {money(inc.get('last_year'))} last year), representing **{metrics.get('income_growth_pct', 'N/A')}% YoY growth**.\n\n"
            f"📍 *Citation: Page {inc.get('page', 'N/A')}*"
        )

    if any(w in q for w in ["profit", "margin", "net income", "bottom line"]):
        prof = metrics.get("profit") or {}
        return (
            f"**Net Profit:** {money(prof.get('this_year'))} (vs {money(prof.get('last_year'))} last year), "
            f"growing at **{metrics.get('profit_growth_pct', 'N/A')}% YoY** with a **Net Profit Margin of {metrics.get('profit_margin_pct', 'N/A')}%**.\n\n"
            f"📍 *Citation: Page {prof.get('page', 'N/A')}*"
        )

    if any(w in q for w in ["asset", "equity", "balance sheet", "solvency"]):
        assets = metrics.get("total_assets") or {}
        equity = metrics.get("total_equity") or {}
        return (
            f"**Balance Sheet Health:** Total Assets stand at **{money(assets.get('this_year'))}** (Page {assets.get('page', 'N/A')}) "
            f"and Total Equity is **{money(equity.get('this_year'))}** (Page {equity.get('page', 'N/A')}). "
            f"The **Equity-to-Assets ratio is {metrics.get('equity_to_assets_pct', 'N/A')}%**."
        )

    if any(w in q for w in ["risk", "penalty", "litigation", "tax", "court", "flag", "audit"]):
        if not flags:
            return "✅ No severe audit or litigation risk flags were detected in this report."
        lines = [f"**Audit Risk Score: {data.get('risk_score', 0)}/100** ({len(flags)} confirmed disclosures):\n"]
        for i, f in enumerate(flags, 1):
            lines.append(f"{i}. **[{f.get('type', '').upper()} - {f.get('severity', '').upper()}]** (Page {f.get('page')}): *\"{f.get('evidence', '')[:180]}...\"*")
        return "\n".join(lines)

    if any(w in q for w in ["summary", "overview", "brief", "highlights"]):
        return f"**Executive Summary:**\n\n{data.get('summary', 'No summary available.')}"

    return (
        f"Based on **{data.get('doc_id')}**, here are the verified figures:\n"
        f"- **Total Income:** {money((metrics.get('total_income') or {}).get('this_year'))} (Page {(metrics.get('total_income') or {}).get('page', 'N/A')})\n"
        f"- **Net Profit:** {money((metrics.get('profit') or {}).get('this_year'))} (Page {(metrics.get('profit') or {}).get('page', 'N/A')})\n"
        f"- **Audit Risk Score:** {data.get('risk_score', 0)}/100 across {len(flags)} flagged disclosures.\n\n"
        f"💡 *Tip: Ask specifically about revenue, profit margins, balance sheet equity, or tax/litigation risks.*"
    )


# Hero Banner
st.markdown("""
    <div class="hero-banner">
        <div class="hero-pill">INSTITUTIONAL FINANCIAL NLP & RISK ENGINE</div>
        <h1 class="hero-title">FinSight AI — Corporate Filing Intelligence</h1>
        <p class="hero-subtitle">Automated Financial Ratio Modeling, Layout-Aware Table Extraction & LLM Risk Auditing with Page Citations</p>
    </div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("## 📂 Filing Ingestion")
    uploaded_file = st.file_uploader("Upload Corporate Annual Report (PDF)", type=["pdf"])
    basis = st.selectbox(
        "Statement Basis",
        ["Consolidated", "Standalone"],
        help="Select whether to extract Consolidated or Standalone financial statement tables.",
    )

    st.divider()
    st.markdown("### ⚙️ Architecture Stack")
    st.info(
        "**1. Parser:** PyMuPDF Keyword-Filtered Tables\n\n"
        "**2. Quant Engine:** Deterministic Python Ratios\n\n"
        "**3. AI Judge:** Local Llama-3.2 (3B) via Ollama\n\n"
        "**4. Cache:** MD5 Hash Instant Reload"
    )

data = None
if uploaded_file is not None:
    try:
        data, from_cache = get_report(uploaded_file.getvalue(), uploaded_file.name, basis)
        if from_cache:
            st.toast("Loaded instantly from MD5 cache!", icon="⚡")
        else:
            st.toast("Full AI analysis completed!", icon="✅")
    except Exception as error:
        st.error(
            f"Analysis failed: {error}. Ensure Ollama is running (`ollama serve`) with `llama3.2:3b` installed."
        )
elif os.path.exists(SAMPLE_PATH):
    with open(SAMPLE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

if data:
    doc_name = data.get("doc_id", "Financial Report")
    metrics = data.get("metrics") or {}
    unit = metrics.get("unit", "INR crore")
    basis_label = metrics.get("basis", "Unspecified")

    # Document Status Strip
    st.markdown(f"**Active Filing:** `{doc_name}` &nbsp;•&nbsp; **Basis:** `{basis_label}` &nbsp;•&nbsp; **Currency Unit:** `{unit}`")

    # Executive Summary Box
    st.markdown("### 📌 AI Executive Narrative")
    summary_text = data.get("summary") or ""
    if not summary_text or "(AI summary comes in the next step)" in summary_text:
        st.warning("AI Executive Summary pending. Run analysis with Ollama active to populate.")
    else:
        st.markdown(f"<div class='summary-card'>{html.escape(summary_text)}</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Workspace Tabs
    tab1, tab2, tab3 = st.tabs([
        "📊 Financial & Risk Analytics",
        f"⚠️ Audit & Litigation Flags ({len(data.get('risk_flags') or [])})",
        "💬 Ask the Filing (Grounded Q&A)"
    ])

    # TAB 1: ANALYTICS
    with tab1:
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

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            render_kpi_card(
                "Total Income",
                money(inc_now),
                metrics.get("income_growth_pct"),
                "% YoY",
                f"📍 Source: Page {inc_page}" if inc_page else "Source: N/A"
            )
        with c2:
            render_kpi_card(
                "Net Profit",
                money(prof_now),
                metrics.get("profit_growth_pct"),
                "% YoY",
                f"📍 Source: Page {prof_page}" if prof_page else "Source: N/A"
            )
        with c3:
            render_kpi_card(
                "Net Profit Margin",
                f"{margin_now}%" if margin_now is not None else "N/A",
                margin_delta,
                " pts YoY",
                "📐 Net Profit / Total Income"
            )
        with c4:
            render_kpi_card(
                "Equity / Assets",
                f"{equity_ratio_now}%" if equity_ratio_now is not None else "N/A",
                equity_ratio_delta,
                " pts YoY",
                f"📍 Assets Page {assets_page}" if assets_page else "Balance Sheet Ratio"
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # Charts Row
        col_bar, col_donut, col_gauge = st.columns([4, 3, 3])

        with col_bar:
            labels, before_vals, now_vals = [], [], []
            for name, before, now in [
                ("Income", inc_before, inc_now),
                ("Net Profit", prof_before, prof_now),
                ("Equity", equity_before, equity_now),
            ]:
                if before is not None and now is not None:
                    labels.append(name)
                    before_vals.append(before)
                    now_vals.append(now)

            if labels:
                fig_bar = go.Figure(data=[
                    go.Bar(name="Last Year", x=labels, y=before_vals, marker_color="#94a3b8", text=before_vals, texttemplate="%{text:,.0f}", textposition="outside"),
                    go.Bar(name="This Year", x=labels, y=now_vals, marker_color="#2563eb", text=now_vals, texttemplate="%{text:,.0f}", textposition="outside"),
                ])
                fig_bar.update_layout(
                    title="YoY Financial Trajectory",
                    barmode="group",
                    height=350,
                    margin=dict(l=15, r=15, t=45, b=20),
                    plot_bgcolor="rgba(0,0,0,0)",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                )
                st.plotly_chart(fig_bar, use_container_width=True)

        with col_donut:
            if assets_now and equity_now and assets_now >= equity_now:
                liabilities_now = assets_now - equity_now
                fig_donut = go.Figure(data=[go.Pie(
                    labels=["Total Equity", "Total Liabilities"],
                    values=[equity_now, liabilities_now],
                    hole=0.58,
                    marker=dict(colors=["#0ea5e9", "#cbd5e1"]),
                    textinfo="percent"
                )])
                fig_donut.update_layout(
                    title="Capital Structure Split",
                    height=350,
                    margin=dict(l=15, r=15, t=45, b=20),
                    legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5),
                )
                st.plotly_chart(fig_donut, use_container_width=True)
            else:
                st.info("Capital structure split requires Total Assets & Equity.")

        with col_gauge:
            risk_score = data.get("risk_score", 0)
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=risk_score,
                number={"suffix": "/100", "font": {"size": 28}},
                title={"text": "Audit Risk Index"},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": "#0f172a"},
                    "steps": [
                        {"range": [0, 35], "color": "#bbf7d0"},
                        {"range": [35, 70], "color": "#fef08a"},
                        {"range": [70, 100], "color": "#fecaca"},
                    ],
                    "threshold": {"line": {"color": "#dc2626", "width": 3}, "thickness": 0.75, "value": 70},
                },
            ))
            fig_gauge.update_layout(height=350, margin=dict(l=25, r=25, t=45, b=20))
            st.plotly_chart(fig_gauge, use_container_width=True)

    # TAB 2: AUDIT RISKS
    with tab2:
        risk_flags = data.get("risk_flags") or []
        if risk_flags:
            sev_filter = st.radio("Filter by Severity:", ["All", "High", "Medium"], horizontal=True)
            for idx, flag in enumerate(risk_flags, start=1):
                sev = str(flag.get("severity", "medium")).capitalize()
                if sev_filter != "All" and sev != sev_filter:
                    continue

                flag_type = str(flag.get("type", "general")).upper()
                badge_sev = "badge-high" if sev.lower() == "high" else "badge-medium"

                with st.expander(f"#{idx} | {flag_type} — {sev} Severity (Page {flag.get('page', 'N/A')})", expanded=(idx == 1)):
                    st.markdown(
                        f"<span class='badge-type'>{html.escape(flag_type)}</span> &nbsp; "
                        f"<span class='{badge_sev}'>{html.escape(sev.upper())} RISK</span> &nbsp; "
                        f"📍 **Filing Page:** `{flag.get('page', 'N/A')}`",
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f"<div class='evidence-box'>{html.escape(str(flag.get('evidence', '')))}</div>",
                        unsafe_allow_html=True,
                    )
        else:
            st.success("✅ Clean Audit Screen: No severe litigation or penalty flags confirmed.")

    # TAB 3: GROUNDED Q&A
    with tab3:
        st.caption("Ask questions about revenue, net profit, margins, balance sheet equity, or legal/tax risk disclosures.")
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = [
                {"role": "assistant", "content": f"Hello! I have loaded **{doc_name}**. Ask me any question about its financial performance or audit risk flags."}
            ]

        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if user_q := st.chat_input("e.g., What is the YoY profit growth or what tax penalties were flagged?"):
            st.session_state.chat_history.append({"role": "user", "content": user_q})
            with st.chat_message("user"):
                st.markdown(user_q)

            reply = answer_question_from_report(user_q, data)
            st.session_state.chat_history.append({"role": "assistant", "content": reply})
            with st.chat_message("assistant"):
                st.markdown(reply)

elif uploaded_file is None:
    st.error("No analysis data found. Ensure `ai_ml_layer/sample_output.json` is present or upload a PDF.")
