import pytest
import pymupdf
from analysis.pdf_reader import read_pdf


def test_rejects_non_pdf_extension(tmp_path):
    file = tmp_path / "note.txt"
    file.write_text("not a PDF")
    with pytest.raises(ValueError, match="must be a PDF"):
        read_pdf(file)


def test_rejects_empty_and_corrupt_pdf(tmp_path):
    empty = tmp_path / "empty.pdf"
    empty.write_bytes(b"")
    with pytest.raises(ValueError):
        read_pdf(empty)
    corrupt = tmp_path / "corrupt.pdf"
    corrupt.write_bytes(b"%PDF-1.4\\n%%EOF")
    with pytest.raises(ValueError, match="Could not open PDF"):
        read_pdf(corrupt)


def test_reads_selectable_text_and_page_number(tmp_path):
    file = tmp_path / "valid.pdf"
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Annual report revenue 100")
    doc.save(file)
    doc.close()
    pages = read_pdf(file, ocr=False)
    assert len(pages) == 1
    assert pages[0]["page"] == 1
    assert "revenue 100" in pages[0]["text"].lower()
