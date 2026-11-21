import re
import ollama
from analysis.judge import MODEL

PROMPT = """You are a financial analyst writing a short executive summary for a reader who is not an expert.
Use ONLY the facts below. Copy every number exactly as written. Do not add any number or fact that is not listed. Do not give investment advice. Do not judge whether the company is good or bad.

Facts:
{facts}

Write one short paragraph of 4 to 6 simple sentences in plain English.
In the first sentence, say which basis the figures are on (for example Standalone means the parent company only).
Cover: income and profit (with growth), the profit margin, the equity to assets ratio, and what the risk screening found.
Say that flagged items still need a human to review them.
End with the risk score out of 100 and say it is only a rough indicator."""


def fmt(x):
    if x == int(x):
        return str(int(x))
    return str(x)


def build_facts(report):
    m = report.metrics
    lines = ["Basis: " + m.basis + ", unit: " + m.unit]
    if m.total_income:
        lines.append("Total income: " + fmt(m.total_income.this_year) + " this year, " + fmt(m.total_income.last_year) + " last year")
    if m.income_growth_pct is not None:
        lines.append("Income growth: " + str(m.income_growth_pct) + " percent")
    if m.profit:
        lines.append("Profit: " + fmt(m.profit.this_year) + " this year, " + fmt(m.profit.last_year) + " last year")
    if m.profit_growth_pct is not None:
        lines.append("Profit growth: " + str(m.profit_growth_pct) + " percent")
    if m.profit_margin_pct is not None:
        lines.append("Profit margin: " + str(m.profit_margin_pct) + " percent")
    if m.equity_to_assets_pct is not None:
        lines.append("Equity to assets: " + str(m.equity_to_assets_pct) + " percent")
    lines.append("Number of flagged risk items: " + str(len(report.risk_flags)))
    for i, f in enumerate(report.risk_flags, start=1):
        lines.append("Flag " + str(i) + ": " + f.type + " on page " + str(f.page) + ": " + f.evidence[:150])
    lines.append("Risk score: " + str(report.risk_score) + " out of 100")
    return "\n".join(lines)


def write_summary(facts):
    response = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": PROMPT.replace("{facts}", facts)}],
        options={"temperature": 0, "num_predict": 300},
    )
    return clean_summary(response["message"]["content"])


def numbers_in(text):
    return set(re.findall(r"\d+(?:\.\d+)?", text.replace(",", "")))


def fallback_summary(report):
    m = report.metrics
    parts = []
    if m.total_income and m.income_growth_pct is not None:
        parts.append("On a " + m.basis + " basis, total income was " + fmt(m.total_income.this_year)
                     + " " + m.unit + ", a change of " + str(m.income_growth_pct) + " percent from last year.")
    if m.profit and m.profit_growth_pct is not None:
        parts.append("Profit was " + fmt(m.profit.this_year) + " " + m.unit
                     + ", a change of " + str(m.profit_growth_pct) + " percent.")
    if m.profit_margin_pct is not None:
        parts.append("The profit margin was " + str(m.profit_margin_pct) + " percent.")
    if m.equity_to_assets_pct is not None:
        parts.append("Equity was " + str(m.equity_to_assets_pct) + " percent of total assets.")
    parts.append("Risk screening flagged " + str(len(report.risk_flags))
                 + " items, which still need a human to review them.")
    parts.append("The risk score is " + str(report.risk_score) + " out of 100, which is only a rough indicator.")
    return " ".join(parts)


def safe_summary(report):
    facts = build_facts(report)
    summary = write_summary(facts)
    extra = numbers_in(summary) - numbers_in(facts)
    if len(extra) == 0:
        return summary, True, []
    return fallback_summary(report), False, sorted(extra)


def clean_summary(text):
    """Remove empty lines and a leading intro line such as 'Here is a short summary:'."""
    lines = []
    for line in text.strip().split("\n"):
        if line.strip():
            lines.append(line.strip())
    if len(lines) > 1 and lines[0].endswith(":"):
        lines = lines[1:]
    return " ".join(lines)
