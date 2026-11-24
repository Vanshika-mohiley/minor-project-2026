from analysis.pdf_reader import read_pdf
from analysis.risk import find_risks, RISK_WORDS

pages = read_pdf("sample_report.pdf")
flags = find_risks(pages)

print("Total flags:", len(flags))

for word in RISK_WORDS:
    pages_hit = []
    for f in flags:
        if f["type"] == word and f["page"] not in pages_hit:
            pages_hit.append(f["page"])
    print(word, ":", len(pages_hit), "pages", pages_hit[:8])

shown = 0
for f in flags:
    if f["severity"] == "high" and shown < 5:
        print("---", f["type"], "| page", f["page"])
        print(f["evidence"])
        shown = shown + 1
