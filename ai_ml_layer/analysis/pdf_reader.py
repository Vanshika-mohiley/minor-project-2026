import pymupdf
from pathlib import Path


def read_pdf(path):
    path = Path(path)

    if path.suffix.lower() != ".pdf":
        raise ValueError("Input file must be a PDF.")

    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {path}")

    pages = []

    with pymupdf.open(path) as pdf:
        if len(pdf) == 0:
            raise ValueError("PDF contains no pages.")

        for number, page in enumerate(pdf, start=1):
            tables = []

            for table in page.find_tables().tables:
                tables.append(table.extract())

            pages.append({
                "page": number,
                "text": page.get_text(),
                "tables": tables,
                "images": len(page.get_images()),
            })

    return pages
