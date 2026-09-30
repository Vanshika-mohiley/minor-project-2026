import pymupdf


def read_pdf(path):
    pdf = pymupdf.open(path)
    pages = []
    for number, page in enumerate(pdf, start=1):
        tables = []
        for t in page.find_tables().tables:
            tables.append(t.extract())
        pages.append({
            "page": number,
            "text": page.get_text(),
            "tables": tables,
            "images": len(page.get_images()),
        })
    return pages
