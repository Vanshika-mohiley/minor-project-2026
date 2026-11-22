import re

_NUMBER = re.compile(r"(?<![A-Za-z])\(?-?\d[\d,]*(?:\.\d+)?\)?")

def to_number(value):
    if value is None:
        return None
    text = str(value).strip().replace("₹", "").replace("INR", "").replace(" ", "")
    if not text or text in {"-", "—", "–"}:
        return None
    negative = text.startswith("(") and text.endswith(")")
    text = text.strip("()").replace(",", "")
    try:
        number = float(text)
    except ValueError:
        return None
    return -abs(number) if negative else number

def _numbers(text):
    found = []
    for match in _NUMBER.finditer(str(text)):
        value = to_number(match.group(0))
        if value is not None:
            found.append(value)
    return found

def _normalise(text):
    return re.sub(r"\s+", " ", str(text or "").strip().lower()).strip(" :.")

def _section_pages(pages, basis):
    basis = (basis or "Unspecified").strip().lower()
    if basis not in {"standalone", "consolidated"}:
        raise ValueError("Select Standalone or Consolidated figures before analysing this report.")

    marker = basis + " financial statements"
    other = ("consolidated" if basis == "standalone" else "standalone") + " financial statements"

    starts = []
    for i, page in enumerate(pages):
        text = _normalise(page.get("text", ""))
        if marker in text and not text.startswith("notes to the " + basis):
            starts.append(i)
    if not starts:
        raise ValueError(f"Could not find the {basis.title()} Financial Statements section in this PDF.")

    start = starts[0]
    end = len(pages)
    for i in range(start + 1, len(pages)):
        text = _normalise(pages[i].get("text", ""))
        if other in text and not text.startswith("notes to the " + basis):
            end = i
            break
    return pages[start:end]

def _pair_from_table(page, label):
    for table in page.get("tables", []):
        for row in table or []:
            cells = [str(cell or "").strip() for cell in row]
            for i, cell in enumerate(cells):
                cell_label = _normalise(cell)
                if cell_label == label or cell_label.startswith(label + " "):
                    values = _numbers(" ".join(cells[i:]))
                    if len(values) >= 2:
                        return values[0], values[1]
    return None

def _pair_from_text(page, label):
    lines = [line.strip() for line in str(page.get("text", "")).splitlines() if line.strip()]
    for i, line in enumerate(lines):
        normal = _normalise(line)
        if normal == label or normal.startswith(label + " "):
            nearby = " ".join(lines[i:i + 6])
            values = _numbers(nearby)
            if len(values) >= 2:
                return values[0], values[1]
    return None

def find_two_values(pages, label):
    label = _normalise(label)
    for page in pages:
        pair = _pair_from_table(page, label)
        if pair is None:
            pair = _pair_from_text(page, label)
        if pair is not None:
            return {"page": page["page"], "this_year": pair[0], "last_year": pair[1]}
    return None

def change_percent(now, before):
    if before is None or before == 0:
        return None
    return (now - before) / abs(before) * 100

def extract_metrics(pages, basis="Unspecified"):
    selected_pages = _section_pages(pages, basis)
    labels = {
        "Total income": "total income",
        "Profit for the year": "profit for the year",
        "Total assets": "total assets",
        "Total equity": "total equity",
    }
    return {name: find_two_values(selected_pages, label) for name, label in labels.items()}
