from analysis.analyze import analyze

def compare_documents(paths, basis="Consolidated", use_ai=False):
    if len(paths) < 2: raise ValueError("Upload at least two PDF reports to compare.")
    if len(paths) > 5: raise ValueError("A maximum of five reports can be compared at once.")
    reports = [analyze(path, basis=basis, use_ai=use_ai) for path in paths]
    rows = []
    for report in reports:
        m = report.metrics
        rows.append({"document": report.doc_id, "basis": m.basis,
            "total_income": m.total_income.this_year if m.total_income else None,
            "profit": m.profit.this_year if m.profit else None,
            "total_assets": m.total_assets.this_year if m.total_assets else None,
            "total_equity": m.total_equity.this_year if m.total_equity else None,
            "profit_margin_pct": m.profit_margin_pct, "equity_to_assets_pct": m.equity_to_assets_pct,
            "risk_score": report.risk_score, "risk_flags": len(report.risk_flags)})
    return rows
