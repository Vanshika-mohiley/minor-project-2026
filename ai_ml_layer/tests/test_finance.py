from analysis.pdf_reader import read_pdf

pages = read_pdf("sample_report.pdf")

KEYWORDS = ["revenue", "total assets", "total equity", "net profit",
            "profit for the year", "borrowings", "total income"]


def table_text(table):
    text = ""
    for row in table:
        for cell in row:
            if cell:
                text = text + " " + cell
    return text.lower()


found = []

for p in pages:
    for table in p["tables"]:
        text = table_text(table)
        hits = 0
        for word in KEYWORDS:
            if word in text:
                hits = hits + 1
        if hits >= 2:
            found.append((p["page"], hits, table))

print("Financial-looking tables found:", len(found))

for page, hits, table in found[:3]:
    print("--- Page", page, "| keywords matched:", hits)
    for row in table[:6]:
        print(row)
