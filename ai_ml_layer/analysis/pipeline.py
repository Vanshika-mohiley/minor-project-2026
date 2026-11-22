from analysis.risk import find_risks
from analysis.judge import judge_snippet

POINTS = {"high": 25, "medium": 10}

def confirm_risks(pages):
    candidates = [
        item for item in find_risks(pages)
        if item.get("severity") in POINTS
    ]
    confirmed = []
    for item in candidates:
        try:
            judgement = judge_snippet(item.get("evidence", ""))
            if judgement.get("real_risk") is not False:
                confirmed.append(item)
        except Exception:
            # Keep the rule-based candidate for human review if the local
            # judge model is unavailable or returns an unexpected response.
            confirmed.append(item)
    return candidates, confirmed

def risk_score(confirmed):
    counts = {}
    for item in confirmed:
        risk_type = item.get("type", "general")
        severity = item.get("severity", "medium")
        counts.setdefault(risk_type, {"count": 0, "severity": severity})
        counts[risk_type]["count"] += 1
        if POINTS.get(severity, 0) > POINTS.get(counts[risk_type]["severity"], 0):
            counts[risk_type]["severity"] = severity

    score = sum(
        POINTS.get(item["severity"], 0) * min(item["count"], 2)
        for item in counts.values()
    )
    return min(score, 100)
