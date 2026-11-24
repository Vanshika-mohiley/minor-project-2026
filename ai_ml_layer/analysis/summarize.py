import re
from analysis.judge import _call_llm

PROMPT = """You are a financial analyst writing a short executive summary for a reader who is not an expert.
Use ONLY the facts below. Copy every number exactly as written. Do not add any number or fact that is not listed. Do not give investment advice.
Facts:
{facts}
Write one short paragraph of 4 to 6 simple sentences in plain English.
State the selected basis, cover income and profit growth, profit margin, equity-to-assets ratio, and risk screening.
Say flagged items need human review. End with the risk score out of 100 and say it is only a rough indicator."""


def fmt(value):
    return str(int(value)) if value == int(value) else str(value)


def build_facts(report):
    m = report.metrics
    lines = [f"Basis: {m.basis}, unit: {m.unit}"]
    if m.total_income:
        lines.append(f"Total income: {fmt(m.total_income.this_year)} this year, {fmt(m.total_income.last_year)} last year")
    if m.income_growth_pct is not None:
        lines.append(f"Income growth: {m.income_growth_pct} percent")
    if m.profit:
        lines.append(f"Profit: {fmt(m.profit.this_year)} this year, {fmt(m.profit.last_year)} last year")
    if m.profit_growth_pct is not None:
        lines.append(f"Profit growth: {m.profit_growth_pct} percent")
    if m.profit_margin_pct is not None:
        lines.append(f"Profit margin: {m.profit_margin_pct} percent")
    if m.equity_to_assets_pct is not None:
        lines.append(f"Equity to assets: {m.equity_to_assets_pct} percent")
    lines.append(f"Number of flagged risk items: {len(report.risk_flags)}")
    for index, flag in enumerate(report.risk_flags, 1):
        lines.append(f"Flag {index}: {flag.type} on page {flag.page}: {flag.evidence[:150]}")
    lines.append(f"Risk score: {report.risk_score} out of 100")
    return "\n".join(lines)


def numbers_in(text):
    return set(re.findall(r"\d+(?:\.\d+)?", str(text).replace(",", "")))


def fallback_summary(report):
    m = report.metrics
    parts = []
    if m.total_income:
        sentence = f"On a {m.basis} basis, total income was {fmt(m.total_income.this_year)} {m.unit}"
        if m.income_growth_pct is not None:
            sentence += f", changing {m.income_growth_pct} percent from last year"
        parts.append(sentence + ".")
    if m.profit:
        sentence = f"Profit was {fmt(m.profit.this_year)} {m.unit}"
        if m.profit_growth_pct is not None:
            sentence += f", changing {m.profit_growth_pct} percent"
        parts.append(sentence + ".")
    if m.profit_margin_pct is not None:
        parts.append(f"The profit margin was {m.profit_margin_pct} percent.")
    if m.equity_to_assets_pct is not None:
        parts.append(f"Equity was {m.equity_to_assets_pct} percent of total assets.")
    parts.append(f"Risk screening flagged {len(report.risk_flags)} items for human review.")
    parts.append(f"The risk score is {report.risk_score} out of 100 and is only a rough indicator.")
    return " ".join(parts)


def safe_summary(report):
    facts = build_facts(report)
    try:
        raw_text = _call_llm(PROMPT.format(facts=facts), json_mode=False, max_tokens=300)
        summary = clean_summary(raw_text)
        if numbers_in(summary) - numbers_in(facts):
            return fallback_summary(report), False, ["unexpected numbers"]
        return summary, True, []
    except Exception as error:
        return fallback_summary(report), False, [str(error)]


def clean_summary(text):
    lines = [line.strip() for line in str(text).strip().splitlines() if line.strip()]
    if len(lines) > 1 and lines[0].endswith(":"):
        lines = lines[1:]
    return " ".join(lines)
