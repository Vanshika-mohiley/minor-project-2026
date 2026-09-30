from analysis.pdf_reader import read_pdf

pages = read_pdf("sample.pdf")
print("Total pages:", len(pages))

for p in pages[:50]:
    print("Page", p["page"], "-> letters:", len(p["text"]))
