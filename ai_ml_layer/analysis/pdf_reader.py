import pymupdf
from pathlib import Path

TABLE_KEYWORDS = (
    "total income", "revenue", "profit", "total assets",
    "total equity", "balance sheet", "liabilities", "standalone", "consolidated"
)

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
            text = page.get_text()
            text_lower = text.lower()
            tables = []

            # Run expensive table detection ONLY on pages with financial keywords
            if any(kw in text_lower for kw in TABLE_KEYWORDS):
                for table in page.find_tables().tables:
                    tables.append(table.extract())

            pages.append({
                "page": number,
                "text": text,
                "tables": tables,
                "images": len(page.get_images()),
            })

    return pages
