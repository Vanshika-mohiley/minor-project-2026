"""Risk indicator aggregation. This is not a credit score or probability."""
from analysis.risk import find_risks

# One contribution per distinct category prevents long reports and repeated
# boilerplate from pushing the dial to 100. The weights are transparent triage
# points, not statistically calibrated risk probabilities.
POINTS = {"high": 20, "medium": 10, "low": 4}


def confirm_risks(pages, use_ai=False):
    candidates = find_risks(pages)
    # Keep the deterministic baseline stable and offline. AI classification can
    # be added explicitly later; it must never silently change the default score.
    return candidates, candidates


def risk_score(findings):
    by_category = {}
    for item in findings or []:
        category = str(item.get("type", "general")).strip().lower()
        severity = str(item.get("severity", "low")).lower()
        points = POINTS.get(severity, 0)
        by_category[category] = max(by_category.get(category, 0), points)
    return min(100, sum(by_category.values()))
