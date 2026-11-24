from pathlib import Path

from analysis.pdf_reader import read_pdf
from analysis.metrics import extract_metrics, change_percent
from analysis.pipeline import confirm_risks, risk_score
from analysis.schemas import AnalysisReport, Metrics, MetricValue, RiskFlag
from analysis.summarize import safe_summary

def to_value(data):
    if data is None:
        return None
    return MetricValue(
        this_year=data["this_year"],
        last_year=data["last_year"],
        page=data["page"],
    )

def analyze(pdf_path, basis="Unspecified"):
    """Analyse a PDF using the explicitly selected financial-statement basis."""
    if basis not in {"Standalone", "Consolidated"}:
        raise ValueError("Please select Standalone or Consolidated figures.")

    pages = read_pdf(pdf_path)
    raw = extract_metrics(pages, basis=basis)

    income = to_value(raw["Total income"])
    profit = to_value(raw["Profit for the year"])
    assets = to_value(raw["Total assets"])
    equity = to_value(raw["Total equity"])

    metrics = Metrics(
        basis=basis,
        total_income=income,
        profit=profit,
        total_assets=assets,
        total_equity=equity,
    )

    if income:
        metrics.income_growth_pct = (
            round(change_percent(income.this_year, income.last_year), 1)
            if income.last_year != 0 else None
        )
    if profit:
        metrics.profit_growth_pct = (
            round(change_percent(profit.this_year, profit.last_year), 1)
            if profit.last_year != 0 else None
        )
    if income and profit and income.this_year != 0:
        metrics.profit_margin_pct = round(profit.this_year / income.this_year * 100, 1)
    if assets and equity and assets.this_year != 0:
        metrics.equity_to_assets_pct = round(equity.this_year / assets.this_year * 100, 1)

    _, confirmed = confirm_risks(pages)
    flags = [
        RiskFlag(
            type=item["type"],
            severity=item["severity"],
            page=item["page"],
            evidence=str(item.get("evidence", ""))[:300],
        )
        for item in confirmed
    ]

    report = AnalysisReport(
        doc_id=Path(pdf_path).name,
        summary="",
        metrics=metrics,
        risk_flags=flags,
        risk_score=risk_score(confirmed),
    )
    summary, _, _ = safe_summary(report)
    report.summary = summary
    return report
