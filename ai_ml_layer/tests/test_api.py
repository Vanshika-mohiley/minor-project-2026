from fastapi.testclient import TestClient

from analysis.api import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_analyze_rejects_non_pdf_upload():
    response = client.post(
        "/analyze",
        data={"basis": "Standalone"},
        files={"file": ("annual-report.txt", b"not a pdf", "text/plain")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Upload a PDF file."


def test_analyze_rejects_invalid_basis():
    response = client.post(
        "/analyze",
        data={"basis": "Other"},
        files={"file": ("annual-report.pdf", b"%PDF-1.4", "application/pdf")},
    )
    assert response.status_code == 422
    assert "Standalone or Consolidated" in response.json()["detail"]


def test_analyze_endpoint_returns_source_grounded_infosys_figures():
    from pathlib import Path

    pdf = Path(__file__).resolve().parents[1] / "sample_report.pdf"
    response = client.post(
        "/analyze",
        data={"basis": "Consolidated"},
        files={"file": ("Infosys_FY2025-26.pdf", pdf.read_bytes(), "application/pdf")},
    )
    assert response.status_code == 200
    result = response.json()
    assert result["doc_id"] == "Infosys_FY2025-26.pdf"
    assert result["metadata"]["company"] == "Infosys"
    assert result["metadata"]["period"] == "2025-26"
    assert result["metrics"]["unit"] == "INR crore"
    assert result["metrics"]["total_income"]["this_year"] == 182972
    assert result["metrics"]["profit"]["this_year"] == 29474
    assert result["metrics"]["total_assets"]["this_year"] == 155967
    assert result["metrics"]["total_equity"]["this_year"] == 93297
    assert result["risk_score"] == 0
