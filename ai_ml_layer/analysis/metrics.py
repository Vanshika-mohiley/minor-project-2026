"""Evidence-first financial-statement extraction for annual reports and 10-K PDFs.

The extractor is deliberately conservative: it searches statement pages (not the
whole report), understands Indian and western digit grouping, and returns None
when a row cannot be tied to a statement with a comparative-period pair.
"""
from __future__ import annotations

import re
from typing import Iterable

# Indian grouping (10,22,401 / 1,23,45,678) and western grouping (1,234,567).
_NUMBER_BODY = r"(?:\d{1,3}(?:,\d{2})*,\d{3}|\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?"
_NUM_RE = re.compile(rf"(?<![A-Za-z0-9])\(?\s*-?\s*{_NUMBER_BODY}\s*\)?(?![A-Za-z0-9])")

# More specific aliases come first. Exact row labels are required at the start
# of a line to avoid accidentally extracting amounts from narrative paragraphs.
ALIASES = {
    "Total income": [
        r"total\s+income", r"total\s+revenues?", r"revenue\s+from\s+operations",
        r"net\s+sales", r"sales\s+and\s+services", r"operating\s+revenues?", r"revenues?",
    ],
    "Profit for the year": [
        r"profit\s+for\s+the\s+(?:year|period)", r"profit\s+after\s+tax(?:ation)?",
        r"net\s+income", r"net\s+profit", r"net\s+earnings",
        r"profit\s+attributable\s+to\s+(?:owners|equity\s+holders)",
        r"income\s+for\s+the\s+(?:year|period)",
    ],
    "Total assets": [r"total\s+assets"],
    "Total equity": [
        # Prefer the statement's overall equity total. In consolidated accounts,
        # this is distinct from "equity attributable to owners" because it also
        # includes non-controlling interests.
        r"total\s+(?:shareholders'?|stockholders'?|owners')?\s*equity(?!\s+attributable)",
        r"total\s+equity(?!\s+attributable)",
        r"total\s+equity\s+attributable\s+to\s+(?:equity\s+)?holders?",
        r"shareholders'?\s+equity", r"stockholders'?\s+equity",
    ],
}

_INCOME_TITLE = re.compile(
    r"^(?:(?:consolidated|standalone|combined|group|parent)\s+)?"
    r"(?:statement|statements)\s+of\s+(?:profit\s+(?:and\s+loss|or\s+loss)|operations?|income|earnings|comprehensive\s+income)"
    r"(?:\s+and\s+other\s+comprehensive\s+income)?$", re.I,
)
_INCOME_ALT_TITLE = re.compile(r"^(?:(?:consolidated|standalone)\s+)?income\s+statement$", re.I)
_BALANCE_TITLE = re.compile(
    r"^(?:(?:consolidated|standalone|combined|group|parent)\s+)?"
    r"(?:balance\s+sheets?|statements?\s+of\s+financial\s+position)$", re.I,
)
_BASIS_HEADER = {
    "Standalone": re.compile(r"\bstandalone\s+financial\s+statements\b", re.I),
    "Consolidated": re.compile(r"\bconsolidated\s+financial\s+statements\b", re.I),
}


def _clean_lines(text: str) -> list[str]:
    return [re.sub(r"\s+", " ", line).strip() for line in str(text or "").splitlines() if line.strip()]


def _num(value: str) -> float | None:
    """Parse one financial number, including Indian commas and parentheses."""
    raw = str(value).strip()
    raw = re.sub(r"^(?:INR|USD|EUR|GBP|Rs\.?|Rupees)\s*", "", raw, flags=re.I)
    raw = raw.replace("₹", "").replace("$", "").replace("€", "").replace("£", "").strip()
    if raw in {"-", "—", "–", ""}:
        return None
    if not re.fullmatch(rf"\(?\s*-?\s*{_NUMBER_BODY}\s*\)?", raw):
        return None
    negative = raw.startswith("(") and raw.endswith(")")
    number = float(raw.strip().strip("()").replace(",", "").replace(" ", ""))
    return -abs(number) if negative else number


def _numbers(text: str) -> list[float]:
    values: list[float] = []
    for match in _NUM_RE.finditer(str(text or "")):
        parsed = _num(match.group(0))
        # Do not mistake year labels or note dates for financial values.
        if parsed is not None and not (1900 <= abs(parsed) <= 2100):
            values.append(parsed)
    return values


def _title_kind(lines: list[str]) -> str | None:
    for line in lines:
        candidate = line.strip().strip(":")
        if _INCOME_TITLE.fullmatch(candidate) or _INCOME_ALT_TITLE.fullmatch(candidate):
            return "income"
        if _BALANCE_TITLE.fullmatch(candidate):
            return "balance"
    return None


def _page_basis(page: dict) -> str | None:
    text = str(page.get("text", ""))
    standalone = bool(_BASIS_HEADER["Standalone"].search(text))
    consolidated = bool(_BASIS_HEADER["Consolidated"].search(text))
    if standalone and not consolidated:
        return "Standalone"
    if consolidated and not standalone:
        return "Consolidated"
    # Some US filings put the basis in the statement title itself.
    lines = _clean_lines(text)
    if any(re.match(r"^standalone\b", line, re.I) for line in lines):
        return "Standalone"
    if any(re.match(r"^consolidated\b", line, re.I) for line in lines):
        return "Consolidated"
    return None


def _statement_title_pages(pages: list[dict], kind: str) -> list[tuple[int, dict]]:
    found = []
    for index, page in enumerate(pages):
        if _title_kind(_clean_lines(page.get("text", ""))) == kind:
            found.append((index, page))
    return found


def detected_basis(pages: list[dict], requested: str = "Standalone") -> str:
    """Choose the requested basis if present in actual statements; otherwise fallback."""
    if requested not in {"Standalone", "Consolidated"}:
        raise ValueError("Choose Standalone or Consolidated.")
    statement_pages = [page for kind in ("income", "balance") for _, page in _statement_title_pages(pages, kind)]
    available = {_page_basis(page) for page in statement_pages} - {None}
    if requested in available:
        return requested
    if len(available) == 1:
        return next(iter(available))
    return requested


def _candidate_pages(pages: list[dict], basis: str, kind: str) -> list[dict]:
    titled = _statement_title_pages(pages, kind)
    if titled:
        typed = [(i, p) for i, p in titled if _page_basis(p) in (None, basis)]
        if not typed:
            typed = titled  # one available statement basis; caller warns on fallback
        # Include adjacent page(s) only to support reports that split the heading
        # and table. Prioritise the actual title page over its neighbours.
        indices: list[int] = []
        for i, _ in typed:
            for j in (i - 1, i, i + 1):
                if 0 <= j < len(pages) and j not in indices:
                    indices.append(j)
        title_indices = {i for i, _ in typed}
        indices.sort(key=lambda i: (0 if i in title_indices else 1, i))
        return [pages[i] for i in indices]

    # Conservative fallback for reports with non-standard statement titles:
    # require several balance/income table cues, not just a stray metric phrase.
    fallback = []
    for page in pages:
        text = str(page.get("text", ""))
        low = text.lower()
        if _page_basis(page) not in (None, basis):
            continue
        if kind == "income":
            cues = sum(bool(re.search(p, low)) for p in (
                r"\b(?:revenue|sales)\b", r"\bprofit\b|\bnet income\b", r"\bexpenses?\b",
                r"\b(?:20\d{2}[-/]\d{2,4}|current year|previous year)\b",
            ))
            if cues >= 3 and len(_clean_lines(text)) >= 8:
                fallback.append(page)
        else:
            cues = sum(bool(re.search(p, low)) for p in (
                r"\btotal assets\b", r"\b(?:total )?liabilities\b", r"\b(?:total )?(?:shareholders'?|stockholders'?|owners')? equity\b",
                r"\b(?:20\d{2}[-/]\d{2,4}|as at|as of)\b",
            ))
            if cues >= 3 and len(_clean_lines(text)) >= 8:
                fallback.append(page)
    return fallback


def _line_label(line: str, aliases: Iterable[str]) -> tuple[str, int] | None:
    clean = re.sub(r"^\s*(?:\(?[a-z0-9]{1,3}\)?[.)]\s+)?", "", line, flags=re.I).strip()
    for alias in aliases:
        match = re.match(rf"^({alias})(?=$|\s|[:(])", clean, re.I)
        if match:
            label = match.group(1)
            # 'Total equity and liabilities' is a balance-sheet total, not equity.
            if re.match(r"total\s+equity\s+and\s+liabilities", clean, re.I):
                continue
            return label, match.end()
    return None


def _values_after_row(lines: list[str], index: int, offset: int) -> list[float] | None:
    values = _numbers(lines[index][offset:])
    if len(values) >= 2:
        return values[:2]

    gathered = list(values)
    numeric_lines = 0
    for next_index in range(index + 1, min(index + 8, len(lines))):
        next_line = lines[next_index]
        found = _numbers(next_line)
        if not found:
            # Stop at the next labelled financial row; do not drift into a note.
            if re.match(r"^[A-Za-z][A-Za-z /()&'-]{2,}$", next_line) and len(gathered) == 0:
                break
            continue
        numeric_lines += 1
        # In many Indian statements a note-reference (e.g. 25) occupies a column
        # between label and values. Ignore that small first cell when paired
        # amounts follow in the next line(s).
        if not gathered and len(found) == 1 and abs(found[0]) <= 99:
            peek = []
            for later in lines[next_index + 1:min(next_index + 4, len(lines))]:
                peek.extend(_numbers(later))
            if len(peek) >= 2:
                continue
        gathered.extend(found)
        if len(gathered) >= 2:
            return gathered[:2]
        if numeric_lines >= 4:
            break
    return None


def _extract_metric(pages: list[dict], basis: str, kind: str, metric: str) -> dict | None:
    candidates = _candidate_pages(pages, basis, kind)
    aliases = ALIASES[metric]
    # Search preferred labels across every candidate page before falling back
    # to less-specific synonyms (Revenue, Net profit, etc.).
    for alias in aliases:
        for page in candidates:
            lines = _clean_lines(page.get("text", ""))
            for i, line in enumerate(lines):
                matched = _line_label(line, [alias])
                if not matched:
                    continue
                _, offset = matched
                values = _values_after_row(lines, i, offset)
                if values is None:
                    continue
                return {
                    "page": int(page.get("page", 1)),
                    "this_year": values[0],
                    "last_year": values[1],
                    "label": line[:180],
                    "confidence": "high" if _title_kind(lines) == kind else "review",
                }
    return None


def extract_metrics(pages: list[dict], basis: str = "Standalone") -> dict:
    if basis not in {"Standalone", "Consolidated"}:
        raise ValueError("Choose Standalone or Consolidated.")
    actual_basis = detected_basis(pages, basis)
    output = {}
    for metric, kind in (
        ("Total income", "income"), ("Profit for the year", "income"),
        ("Total assets", "balance"), ("Total equity", "balance"),
    ):
        output[metric] = _extract_metric(pages, actual_basis, kind, metric)
    return output


def detect_metadata(pages: list[dict]) -> dict:
    first_text = "\n".join(str(p.get("text", "")) for p in pages[:12])
    statement_text = "\n".join(str(p.get("text", "")) for kind in ("income", "balance") for _, p in _statement_title_pages(pages, kind))
    evidence = statement_text or first_text
    unit = "Unspecified"
    for pattern, value in (
        (r"\b(?:in|amounts? in)\s+(?:₹|Rs\.?|INR|[`'])?\s*(?:crores?|cr\.)\b|\bC\s+in\s+crore\b", "crore"),
        (r"\b(?:in|amounts? in)\s+(?:₹|Rs\.?|INR)?\s*(?:lakhs?|lacs?)\b", "lakh"),
        (r"\b(?:in|amounts? in)\s+(?:\$|USD)?\s*(?:billions?|bn)\b", "billions"),
        (r"\b(?:in|amounts? in)\s+(?:₹|Rs\.?|INR|\$|USD)?\s*(?:millions?|mn)\b", "millions"),
        (r"\b(?:in|amounts? in)\s+(?:₹|Rs\.?|INR)?\s*(?:thousands?|000s)\b", "thousands"),
    ):
        if re.search(pattern, evidence, re.I):
            unit = value
            break

    currency = "Unspecified"
    # Prefer explicit currency names/symbols. A stray '$' can occur in a
    # multinational report's director biographies even when statements are INR.
    for pattern, code in ((r"₹|\bINR\b|\bRs\.?\b|\brupees\b|\bindian rupees\b", "INR"),
                          (r"\bUSD\b|\bUS dollars?\b", "USD"),
                          (r"€|\bEUR\b", "EUR"), (r"£|\bGBP\b", "GBP")):
        if re.search(pattern, evidence, re.I):
            currency = code
            break
    if currency == "Unspecified" and "$" in evidence:
        currency = "USD"
    if currency == "Unspecified" and unit == "crore":
        currency = "INR"  # 'crore' is an Indian-reporting unit; disclose as inferred.

    company = "Unidentified company"
    lines = _clean_lines(first_text)[:160]
    # Legal-entity names are better identifiers than headings such as
    # 'Reliance at a Glance' or 'Apple at Work'.
    for line in lines:
        if 4 <= len(line) <= 110 and re.search(r"\b(?:incorporated|inc\.?|corporation|corp\.?|limited|ltd\.?|plc|llc)\b", line, re.I):
            cleaned = re.sub(r"^\d+\s+", "", line).strip()
            if not re.search(r"annual report|integrated annual report|corporate overview", cleaned, re.I):
                company = cleaned[:110]
                break
    if company == "Unidentified company":
        for brand in ("Infosys", "Reliance Industries", "Apple", "Microsoft", "Tata Consultancy Services", "Wipro", "HCL Technologies", "Alphabet", "Google"):
            match = re.search(rf"\b{re.escape(brand)}\b", first_text, re.I)
            if match:
                company = brand
                break
    period = "Unidentified"
    match = re.search(r"\bFY\s*(20\d{2})(?:\s*[-/]\s*(\d{2,4}))?\b", first_text, re.I)
    if not match:
        match = re.search(r"\b(20\d{2})\s*[-/]\s*(\d{2,4})\b", first_text)
    if match:
        period = match.group(1) + (f"-{match.group(2)}" if match.group(2) else "")
    else:
        years = re.findall(r"\b20\d{2}\b", first_text)
        if years:
            period = years[0]
    return {"company": company, "currency": currency, "unit": unit, "period": period}


def change_percent(now: float | None, before: float | None) -> float | None:
    if now is None or before in (None, 0):
        return None
    return (now - before) / abs(before) * 100


def to_number(value: str) -> float | None:
    return _num(value)
