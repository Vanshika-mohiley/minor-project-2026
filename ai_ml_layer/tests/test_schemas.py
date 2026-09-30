from analysis.schemas import AnalysisReport, Metrics

report = AnalysisReport(
    summary="This is a test summary",
    metrics=Metrics(revenue=1200.5, net_income=88.2),
)
print(report)