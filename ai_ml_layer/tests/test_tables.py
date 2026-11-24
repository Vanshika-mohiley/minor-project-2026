from analysis.pdf_reader import read_pdf

pages = read_pdf("sample_report.pdf")

pages_with_tables = 0
pages_with_images = 0

for p in pages:
    if len(p["tables"]) > 0:
        pages_with_tables = pages_with_tables + 1
    if p["images"] > 0:
        pages_with_images = pages_with_images + 1

print("Pages with tables:", pages_with_tables)
print("Pages with images:", pages_with_images)

for p in pages:
    if len(p["tables"]) > 0:
        print("First table is on page", p["page"])
        for row in p["tables"][0][:5]:
            print(row)
        break
