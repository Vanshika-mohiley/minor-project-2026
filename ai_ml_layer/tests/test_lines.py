from analysis.pdf_reader import read_pdf

pages = read_pdf("sample_report.pdf")

WANTED = ["total income", "profit for the year", "total assets", "total equity"]

results = []

for p in pages:
    lines = p["text"].split("\n")
    for i in range(len(lines)):
        low = lines[i].lower()
        for word in WANTED:
            if word in low:
                joined = " | ".join(lines[i:i + 4])
                results.append("Page " + str(p["page"]) + ": " + joined)

print("Total matches:", len(results))
for r in results[:15]:
    print(r)
