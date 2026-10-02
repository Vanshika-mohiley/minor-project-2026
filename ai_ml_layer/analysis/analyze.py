from analysis.pdf_reader import read_pdf
from analysis.metrics import extract_metrics, change_percent
from analysis.pipeline import confirm_risks, risk_score
from analysis.schemas import AnalysisReport, Metrics, MetricValue, RiskFlag


def to_value(d):
    if d is None:
        return None
    return MetricValue(this_year=d["this_year"], last_year=d["last_year"], page=d["page"])


def analyze(pdf_path, basis="Standalone"):
    pages = read_pdf(pdf_path)
    raw = extract_metrics(pages)

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

    if income and profit:
        metrics.income_growth_pct = round(change_percent(income.this_year, income.last_year), 1)
        metrics.profit_growth_pct = round(change_percent(profit.this_year, profit.last_year), 1)
        metrics.profit_margin_pct = round(profit.this_year / income.this_year * 100, 1)
    if assets and equity:
        metrics.equity_to_assets_pct = round(equity.this_year / assets.this_year * 100, 1)

    candidates, confirmed = confirm_risks(pages)
    flags = []
    for f in confirmed:
        flags.append(RiskFlag(
            type=f["type"],
            severity=f["severity"],
            page=f["page"],
            evidence=f["evidence"][:300],
        ))

    return AnalysisReport(
        doc_id=pdf_path.split("/")[-1],
        summary="(AI summary comes in the next step)",
        metrics=metrics,
        risk_flags=flags,
        risk_score=risk_score(confirmed),
    )
