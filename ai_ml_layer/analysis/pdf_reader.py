"""Fast, resilient PDF ingestion with selectable-text and optional OCR support."""
from pathlib import Path
import re
import pymupdf


def _ocr_page(page, languages="eng"):
    try:
        import io
        import pytesseract
        from PIL import Image
        pix = page.get_pixmap(matrix=pymupdf.Matrix(2, 2), alpha=False)
        return pytesseract.image_to_string(Image.open(io.BytesIO(pix.tobytes("png"))), lang=languages)
    except Exception:
        return ""


def read_pdf(path, ocr=True, ocr_languages="eng", min_text_chars=25):
    path = Path(path)
    if path.suffix.lower() != ".pdf":
        raise ValueError("Input file must be a PDF.")
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError("PDF file is missing or empty.")
    try:
        document = pymupdf.open(path)
    except Exception as exc:
        raise ValueError(f"Could not open PDF. It may be damaged or not a valid PDF: {exc}") from exc

    pages = []
    with document as pdf:
        if pdf.is_encrypted and not pdf.authenticate(""):
            raise ValueError("Password-protected PDF. Upload an unlocked PDF.")
        if len(pdf) == 0:
            raise ValueError("PDF has no pages.")
        for page_number, page in enumerate(pdf, start=1):
            # Preserve the PDF content-stream order. In multi-column financial
            # tables, sorting geometrically can merge the current/prior columns.
            text = page.get_text("text") or ""
            ocr_used = False
            ocr_warning = None
            if ocr and len(re.sub(r"\s", "", text)) < min_text_chars:
                scanned = _ocr_page(page, ocr_languages)
                if scanned.strip():
                    text, ocr_used = scanned, True
                else:
                    ocr_warning = f"Page {page_number}: no selectable text; OCR is unavailable or returned no readable text."
            pages.append({
                "page": page_number,
                "text": text,
                "tables": [],  # Text lines retain table row/column order for this baseline.
                "images": len(page.get_images()),
                "ocr_used": ocr_used,
                "ocr_warning": ocr_warning,
            })
    return pages
