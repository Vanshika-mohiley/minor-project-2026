def to_number(text):
    t = text.strip().replace(",", "")
    negative = t.startswith("(") and t.endswith(")")
    t = t.strip("()")
    try:
        value = float(t)
    except ValueError:
        return None
    if negative:
        value = -value
    return value


def find_two_values(pages, label):
    for p in pages:
        lines = p["text"].split("\n")
        for i in range(len(lines)):
            if lines[i].strip().lower() == label:
                numbers = []
                for nxt in lines[i + 1:i + 5]:
                    n = to_number(nxt)
                    if n is not None:
                        numbers.append(n)
                if len(numbers) >= 2:
                    return {
                        "page": p["page"],
                        "this_year": numbers[0],
                        "last_year": numbers[1],
                    }
    return None


def change_percent(now, before):
    return (now - before) / before * 100


def extract_metrics(pages):
    items = {
        "Total income": "total income",
        "Profit for the year": "profit for the year",
        "Total assets": "total assets",
        "Total equity": "total equity",
    }
    result = {}
    for name, label in items.items():
        result[name] = find_two_values(pages, label)
    return result
