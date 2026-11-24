import pytest

from analysis.metrics import to_number, change_percent, extract_metrics
from analysis.schemas import AnalysisReport

def test_indian_number_format():
    assert to_number("1,55,310") == 155310

def test_negative_number():
    assert to_number("(45)") == -45

def test_income_growth():
    assert round(change_percent(155310, 141374), 1) == 9.9

def test_zero_previous_year():
    assert change_percent(100, 0) is None

def test_negative_growth():
    assert round(change_percent(80, 100), 1) == -20.0

def test_empty_report():
    report = AnalysisReport(doc_id="test", summary="")
    assert report.risk_score == 0
    assert report.risk_flags == []

def test_basis_required_when_unspecified():
    pages = [{"page": 1, "text": "Standalone Financial Statements"}]
    with pytest.raises(ValueError):
        extract_metrics(pages, basis="Unspecified")

def test_extracts_selected_section_only():
    pages = [
        {"page": 1, "text": "Standalone Financial Statements\nTotal income\n100\n90\nProfit for the year\n10\n9\nTotal assets\n200\n180\nTotal equity\n120\n100", "tables": []},
        {"page": 2, "text": "Consolidated Financial Statements\nTotal income\n500\n450\nProfit for the year\n50\n45\nTotal assets\n900\n800\nTotal equity\n500\n450", "tables": []},
    ]
    result = extract_metrics(pages, basis="Consolidated")
    assert result["Total income"]["this_year"] == 500
    assert result["Total assets"]["this_year"] == 900
