"""Regression checks against the Infosys FY2025-26 PDF bundled with the project."""
from pathlib import Path

import pytest

from analysis.analyze import analyze

PDF = Path(__file__).resolve().parents[1] / "sample_report.pdf"
pytestmark = pytest.mark.skipif(not PDF.exists(), reason="Bundled sample report is not present")


@pytest.mark.parametrize(
    ("basis", "expected"),
    [
        (
            "Standalone",
            {
                "total_income": (155310, 141374),
                "profit": (29211, 25568),
                "total_assets": (126691, 124936),
                "total_equity": (80874, 87332),
            },
        ),
        (
            "Consolidated",
            {
                "total_income": (182972, 166590),
                "profit": (29474, 26750),
                "total_assets": (155967, 148903),
                "total_equity": (93297, 96203),
            },
        ),
    ],
)
def test_bundled_infosys_report_extracts_correct_metrics(basis, expected):
    report = analyze(str(PDF), basis=basis, ocr=False)
    metrics = report.metrics

    assert report.metadata["company"] == "Infosys"
    assert report.metadata["period"] == "2025-26"
    assert metrics.basis == basis
    assert metrics.unit == "INR crore"

    for name, (current, previous) in expected.items():
        metric = getattr(metrics, name)
        assert metric is not None, name
        assert metric.this_year == current, (basis, name, metric.model_dump())
        assert metric.last_year == previous, (basis, name, metric.model_dump())
        assert metric.page > 0
        assert metric.label

    assert 0 <= report.risk_score <= 100
    assert report.risk_score < 100
