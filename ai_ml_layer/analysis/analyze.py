from pathlib import Path
from analysis.pdf_reader import read_pdf
from analysis.metrics import extract_metrics, change_percent, detect_metadata, detected_basis
from analysis.risk import find_risks
from analysis.pipeline import risk_score
from analysis.schemas import AnalysisReport, Metrics, MetricValue, RiskFlag
from analysis.summarize import fallback_summary


def _value(data):
    return MetricValue(**data) if data else None


def analyze(pdf_path, basis="Standalone", use_ai=False, ocr=True, doc_name=None):
    if basis not in {"Standalone", "Consolidated"}:
        raise ValueError("Please select Standalone or Consolidated figures.")
    pages = read_pdf(pdf_path, ocr=ocr)
    metadata = detect_metadata(pages)
    actual_basis = detected_basis(pages, basis)
    raw = extract_metrics(pages, actual_basis)
    income, profit, assets, equity = (_value(raw[k]) for k in ("Total income", "Profit for the year", "Total assets", "Total equity"))
    unit_parts = [metadata["currency"], metadata["unit"]]
    unit = " ".join(x for x in unit_parts if x != "Unspecified") or "Unit not identified"
    metrics = Metrics(basis=actual_basis, unit=unit, total_income=income, profit=profit, total_assets=assets, total_equity=equity)
    if income:
        metrics.income_growth_pct = round(change_percent(income.this_year, income.last_year), 1)
    if profit:
        metrics.profit_growth_pct = round(change_percent(profit.this_year, profit.last_year), 1)
    if income and profit and income.this_year:
        metrics.profit_margin_pct = round(profit.this_year / income.this_year * 100, 1)
    if assets and equity and assets.this_year:
        metrics.equity_to_assets_pct = round(equity.this_year / assets.this_year * 100, 1)

    candidates = find_risks(pages)
    flags = [RiskFlag(**item) for item in candidates[:80]]
    score = risk_score(candidates)
    warnings = []
    if metadata["currency"] == "Unspecified":
        warnings.append("Currency was not identified confidently. The app does not convert currencies.")
    if metadata["unit"] == "Unspecified":
        warnings.append("Financial statement unit was not identified confidently. Verify the unit printed on the source statements.")
    if actual_basis != basis:
        warnings.append(f"The requested {basis} statements were not located; the available {actual_basis} statements were used instead.")
    if assets and equity:
        if assets.this_year <= 0:
            warnings.append("Total assets are zero or negative. Verify the extracted balance-sheet row before using ratios.")
        elif equity.this_year < 0 or equity.this_year > assets.this_year:
            warnings.append("Extracted total equity is outside the expected 0-to-total-assets range. Verify the source row and reporting basis.")
    if metrics.profit_margin_pct is not None and abs(metrics.profit_margin_pct) > 100:
        warnings.append("Calculated net profit margin is outside ±100%. Verify that income and profit rows use the same basis and units.")
    missing = [name for name, value in (("income", income), ("profit", profit), ("assets", assets), ("equity", equity)) if value is None]
    if missing:
        warnings.append("Could not confidently extract: " + ", ".join(missing) + ". Missing figures are left blank, not guessed.")
    for page in pages:
        if page.get("ocr_warning"):
            warnings.append(page["ocr_warning"])
        if page.get("ocr_used"):
            warnings.append(f"OCR was used on page {page['page']}; verify its figures manually.")
    # Keep warnings distinct.
    warnings = list(dict.fromkeys(warnings))
    report = AnalysisReport(
        doc_id=Path(doc_name or pdf_path).name, summary="", metrics=metrics, risk_flags=flags,
        risk_score=score, pages=len(pages), extraction_warnings=warnings, metadata=metadata,
    )
    report.summary = fallback_summary(report)
    return report
