"""Optional end-to-end regression against a user-supplied public annual report."""
import os
import pytest
from analysis.analyze import analyze

PDF = os.environ.get("FINSIGHT_TEST_PDF")
pytestmark = pytest.mark.skipif(not PDF, reason="Set FINSIGHT_TEST_PDF to run real-report regression")


def test_real_pdf_extracts_at_least_one_financial_metric():
    report = analyze(PDF, basis="Standalone", ocr=False)
    metrics = report.metrics
    assert any((metrics.total_income, metrics.profit, metrics.total_assets, metrics.total_equity))
    assert 0 <= report.risk_score <= 100
    for value in (metrics.total_income, metrics.profit, metrics.total_assets, metrics.total_equity):
        if value:
            assert value.page > 0
            assert value.label
