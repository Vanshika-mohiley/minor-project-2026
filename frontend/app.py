import hashlib, json, os, sys, tempfile
from pathlib import Path
import streamlit as st
import plotly.graph_objects as go

ROOT=Path(__file__).resolve().parents[1]
ML=ROOT/"ai_ml_layer"
CACHE=ML/"cache"
sys.path.insert(0,str(ML))

st.set_page_config(page_title="FinSight AI | Corporate Filing Intelligence",page_icon="📊",layout="wide",initial_sidebar_state="expanded")
st.markdown("""
<style>
:root{color-scheme:dark}
.stApp{background:#171717;color:#f4f6fb}
section[data-testid="stSidebar"]{background:#202020;border-right:1px solid #353535}
.block-container{padding-top:2rem;max-width:1500px}
.hero{background:linear-gradient(115deg,#202b40,#174b79);border:1px solid #285d91;border-radius:16px;padding:30px 32px;margin-bottom:18px}
.eyebrow{display:inline-block;color:#4fc3ff;border:1px solid #176b9c;background:#14364d;padding:5px 12px;border-radius:20px;font-size:11px;font-weight:700;letter-spacing:.4px}
.hero h1{font-size:30px;margin:18px 0 8px;color:white}.hero p{color:#a9c3e6;margin:0}
.metric-card{background:#242b35;border:1px solid #3a4656;border-radius:12px;padding:18px 20px;min-height:122px}
.metric-label{font-size:11px;color:#a8bad0;text-transform:uppercase;letter-spacing:.8px}.metric-value{font-size:27px;font-weight:750;color:#fff;margin:7px 0}.metric-foot{font-size:11px;color:#9bb0c8}
.section-title{font-size:22px;font-weight:700;margin:24px 0 12px}
.summary{background:#f5f7fb;color:#142033;border-left:5px solid #2d73f5;border-radius:10px;padding:18px 22px;line-height:1.65}
.smallmuted{color:#a9b5c7;font-size:12px}
div[data-testid="stTabs"] button{color:#c7d2e2}
</style>
""",unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## 📂 Filing Ingestion")
    uploaded=st.file_uploader("Upload Corporate Annual Report (PDF)",type=["pdf"],help="PDF only · maximum 200 MB")
    basis=st.selectbox("Statement Basis",["Choose basis…","Standalone","Consolidated"],index=0)
    st.divider()
    st.markdown("### ⚙️ Architecture Stack")
    st.markdown("**1. Document Reader**  \nPyMuPDF text extraction + OCR fallback")
    st.markdown("**2. Financial Engine**  \nDeterministic Python calculations")
    st.markdown("**3. Risk Screening**  \nEvidence-backed keyword triage")
    st.markdown("**4. Retrieval**  \nPage-grounded filing Q&A")
    st.divider()
    st.caption("No sample figures are loaded. Results appear only after a report is uploaded and analysed.")

st.markdown('<div class="hero"><span class="eyebrow">INSTITUTIONAL FINANCIAL NLP & RISK ENGINE</span><h1>FinSight AI — Corporate Filing Intelligence</h1><p>Automated financial ratio modelling, layout-aware statement extraction and explainable risk screening with page citations</p></div>',unsafe_allow_html=True)

if not uploaded:
    st.markdown("### Welcome to FinSight AI")
    st.info("Upload a company's annual report from the left panel and select Standalone or Consolidated statements to begin. No demo or placeholder numbers are displayed.")
    c1,c2,c3=st.columns(3)
    for col,head,body in [(c1,"📄 Document ingestion","Extracts selectable PDF text and uses OCR only for scanned pages."),(c2,"📊 Financial analytics","Calculates income growth, profit growth, margins and capital structure from identified statements."),(c3,"🔎 Explainable screening","Shows risk-related passages with source page references for human review.")]:
        with col: st.markdown(f"<div class='metric-card'><b>{head}</b><p class='smallmuted'>{body}</p></div>",unsafe_allow_html=True)
    st.stop()

if basis=="Choose basis…":
    st.warning("Please select whether you want Standalone or Consolidated figures.")
    st.stop()

@st.cache_data(show_spinner=False,max_entries=12)
def analyse_bytes(data,name,selected_basis):
    from analysis.analyze import analyze
    with tempfile.NamedTemporaryFile(suffix=".pdf",delete=False) as f:
        f.write(data); path=f.name
    try: return analyze(path,basis=selected_basis).model_dump()
    finally: os.unlink(path)

file_bytes=uploaded.getvalue()
if len(file_bytes)>200*1024*1024:
    st.error("This PDF exceeds the 200 MB upload limit."); st.stop()
try:
    with st.spinner("Reading PDF pages, locating the selected financial statements and validating extracted figures…"):
        data=analyse_bytes(file_bytes,uploaded.name,basis)
except Exception as e:
    st.error(f"Analysis could not be completed: {e}")
    st.caption("Try an unlocked PDF with selectable text. Scanned PDFs require Tesseract OCR to be installed on the server.")
    st.stop()

m=data.get("metrics",{})
actual_basis=(m.get("basis") or basis)
st.success(f"Analysis completed · {uploaded.name} · {actual_basis} basis")
meta=data.get("metadata",{})
unit=m.get("unit","Unit not identified")
st.caption(f"Active filing: **{uploaded.name}**  ·  Basis: **{actual_basis}**  ·  Company: **{meta.get('company','Unidentified')}**  ·  Period: **{meta.get('period','Unidentified')}**  ·  Units: **{unit}**")
for warning in data.get("extraction_warnings",[]): st.warning(warning)

def val(k):
    d=m.get(k) or {}; return d.get("this_year"),d.get("last_year"),d.get("page")
def money(x): return "Not found" if x is None else f"{x:,.2f}"
def growth(x): return "Not available" if x is None else f"{x:+.1f}% YoY"
def card(label,value,foot):
    st.markdown(f"<div class='metric-card'><div class='metric-label'>{label}</div><div class='metric-value'>{value}</div><div class='metric-foot'>{foot}</div></div>",unsafe_allow_html=True)

st.markdown("<div class='section-title'>📌 Executive Narrative</div>",unsafe_allow_html=True)
st.markdown(f"<div class='summary'>{data.get('summary') or 'A narrative could not be generated from the extracted figures. Review the source statements below.'}</div>",unsafe_allow_html=True)

inc,inc0,ip=val("total_income"); prof,prof0,pp=val("profit"); assets,assets0,ap=val("total_assets"); equity,equity0,ep=val("total_equity")
cols=st.columns(4)
items=[("TOTAL INCOME",money(inc),f"{growth(m.get('income_growth_pct'))} · Page {ip or '—'}"),("NET PROFIT",money(prof),f"{growth(m.get('profit_growth_pct'))} · Page {pp or '—'}"),("NET PROFIT MARGIN",("Not available" if m.get('profit_margin_pct') is None else f"{m['profit_margin_pct']:.1f}%"),"Net profit ÷ total income"),("EQUITY / ASSETS",("Not available" if m.get('equity_to_assets_pct') is None else f"{m['equity_to_assets_pct']:.1f}%"),f"Page {ep or '—'} / {ap or '—'}")]
for c,(a,b,d) in zip(cols,items):
    with c: card(a,b,d)

st.markdown("<div class='section-title'>📈 Financial & Risk Analytics</div>",unsafe_allow_html=True)
tab1,tab2,tab3=st.tabs(["📊 Financial Analytics","⚠️ Audit & Risk Flags","💬 Ask the Filing"])
with tab1:
    left,right=st.columns([1.35,1])
    with left:
        labels=[]; prior=[]; current=[]
        for label,a,b in [("Total Income",inc0,inc),("Net Profit",prof0,prof),("Total Assets",assets0,assets),("Total Equity",equity0,equity)]:
            if a is not None and b is not None: labels.append(label);prior.append(a);current.append(b)
        if labels:
            fig=go.Figure([go.Bar(name="Previous year",x=labels,y=prior,marker_color="#92a8c5"),go.Bar(name="Current year",x=labels,y=current,marker_color="#2f73ed")])
            fig.update_layout(title=f"Comparative amounts ({unit})",barmode="group",height=360,paper_bgcolor="#171717",plot_bgcolor="#171717",font_color="#e7edf7",margin=dict(l=10,r=10,t=45,b=20),legend=dict(orientation="h",y=1.12))
            st.plotly_chart(fig,use_container_width=True)
        else: st.warning("No comparable year-on-year figures were extracted.")
    with right:
        if equity is not None and assets and 0 <= equity <= assets:
            fig=go.Figure(go.Pie(labels=["Total Equity","Total Liabilities"],values=[equity,assets-equity],hole=.55,marker_colors=["#18a9e8","#c7d4e4"],textinfo="percent"))
            fig.update_layout(title="Capital Structure Split",height=360,paper_bgcolor="#171717",font_color="#e7edf7",margin=dict(l=5,r=5,t=40,b=5),showlegend=True)
            st.plotly_chart(fig,use_container_width=True)
        elif equity is not None and assets:
            st.warning("Capital structure chart hidden because extracted equity does not reconcile within total assets. Review the figures and source pages.")
        else: st.info("Capital structure chart requires both total equity and total assets.")
    st.markdown("#### Extracted figures & source pages")
    rows=[]
    for label,k in [("Total Income","total_income"),("Net Profit","profit"),("Total Assets","total_assets"),("Total Equity","total_equity")]:
        d=m.get(k) or {}; rows.append({"Metric":label,f"Current year ({unit})":d.get("this_year"),f"Previous year ({unit})":d.get("last_year"),"PDF page":d.get("page"),"Extracted label":d.get("label"),"Confidence":d.get("confidence")})
    st.dataframe(rows,use_container_width=True,hide_index=True)
    st.caption("Ratios are computed from extracted statement values. Missing values are left blank rather than guessed.")
with tab2:
    flags=data.get("risk_flags") or []
    score=max(0,min(100,int(data.get("risk_score") or 0)))
    gauge_col, detail_col = st.columns([1, 1.6])
    with gauge_col:
        gauge = go.Figure(go.Indicator(
            mode="gauge+number", value=score,
            title={"text": "Disclosure Signal Index (0–100)"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "#4aa3ff"},
                "steps": [
                    {"range": [0, 20], "color": "#1f6b4b"},
                    {"range": [20, 50], "color": "#8b792a"},
                    {"range": [50, 75], "color": "#9a5728"},
                    {"range": [75, 100], "color": "#8d3434"},
                ],
            },
        ))
        gauge.update_layout(height=280, paper_bgcolor="#171717", font_color="#e7edf7", margin=dict(l=24,r=24,t=55,b=10))
        st.plotly_chart(gauge, use_container_width=True)
        st.caption(f"{data.get('risk_score_label','Disclosure signal index (0–100)')}. Rule-based indicator, not a probability, credit rating or investment recommendation. Repeated passages in one category count once.")
    with detail_col:
        st.warning("Every highlighted passage needs human review. A zero score means this rule set did not identify a qualifying passage; it does not mean the company has no risk.")
        if not flags:
            st.success("No qualifying adverse-disclosure patterns were identified by the current screening rules.")
        else:
            st.write(f"{len(flags)} potentially relevant passage(s) identified")
            for i,f in enumerate(flags,1):
                with st.expander(f"{i}. {f.get('type','Risk item').title()} · {f.get('severity','review').title()} · PDF page {f.get('page','—')}"):
                    st.write(f.get("evidence",""))
with tab3:
    q=st.text_input("Ask a question about this filing",placeholder="e.g. What was consolidated total income in FY 2024-25?")
    if st.button("Find answer",disabled=not q.strip()):
        from analysis.pdf_reader import read_pdf
        from analysis.qa import answer_question
        with tempfile.NamedTemporaryFile(suffix=".pdf",delete=False) as f: f.write(file_bytes); path=f.name
        try:
            with st.spinner("Searching relevant report pages…"): ans=answer_question(read_pdf(path,ocr=False),q)
            st.write(ans["answer"])
        finally: os.unlink(path)

st.divider()
st.caption("FinSight AI is an academic decision-support prototype. Verify extracted figures against the audited annual report before relying on them.")
