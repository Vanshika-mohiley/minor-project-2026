"""Factual, deterministic summary from extracted values and evidence."""

def _fmt(value):
    value = float(value)
    return f"{int(value):,}" if value.is_integer() else f"{value:,.2f}"


def fallback_summary(report):
    metrics = report.metrics
    parts = [f"The analysis used {metrics.basis} financial statements. Reported units: {metrics.unit}."]
    for label, item in (("Total income", metrics.total_income), ("Profit", metrics.profit)):
        if item:
            parts.append(f"{label} was {_fmt(item.this_year)} in the current period versus {_fmt(item.last_year)} in the prior period (PDF page {item.page}).")
        else:
            parts.append(f"{label} could not be confidently extracted from the financial statements.")
    if metrics.profit_margin_pct is not None:
        parts.append(f"The calculated net profit margin was {metrics.profit_margin_pct:.1f}%.")
    if metrics.equity_to_assets_pct is not None:
        parts.append(f"Equity represented {metrics.equity_to_assets_pct:.1f}% of total assets.")
    parts.append(
        f"The disclosure screening identified {len(report.risk_flags)} passage(s) for human review. "
        f"Its indicative signal index is {report.risk_score}/100; this is not a probability, credit rating, or audit opinion."
    )
    return " ".join(parts)
