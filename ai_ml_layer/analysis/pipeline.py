from analysis.risk import find_risks, RISK_WORDS
from analysis.judge import judge_snippet

POINTS = {"high": 25, "medium": 10}


def confirm_risks(pages):
    candidates = []
    for f in find_risks(pages):
        if f["severity"] != "low":
            candidates.append(f)

    confirmed = []
    for f in candidates:
        result = judge_snippet(f["evidence"])
        if result["real_risk"] is not False:
            confirmed.append(f)
    return candidates, confirmed


def risk_score(confirmed):
    counts = {}
    for f in confirmed:
        counts[f["type"]] = counts.get(f["type"], 0) + 1

    score = 0
    for word, n in counts.items():
        severity = RISK_WORDS[word]
        score = score + POINTS[severity] * min(n, 2)
    return min(score, 100)
