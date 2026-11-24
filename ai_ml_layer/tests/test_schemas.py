from analysis.schemas import AnalysisReport, Metrics

report = AnalysisReport(
    doc_id="demo",
    summary="This is a test summary",
    metrics=Metrics(income_growth_pct=9.9),
)
print(report)
