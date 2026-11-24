from analysis.risk import find_risks
from analysis.judge import judge_snippet, judge_snippets_batch

POINTS = {"high": 25, "medium": 10}


def confirm_risks(pages):
    candidates = [
        item for item in find_risks(pages)
        if item.get("severity") in POINTS
    ]
    if not candidates:
        return [], []

    # Deduplicate identical evidence strings before sending to LLM
    seen = set()
    unique_candidates = []
    for item in candidates:
        ev = item.get("evidence", "").strip()
        if ev not in seen:
            seen.add(ev)
            unique_candidates.append(item)

    # Cap at top 15 candidates for fast single-pass latency
    batch_items = unique_candidates[:15]
    confirmed = []

    try:
        judgements = judge_snippets_batch([i.get("evidence", "") for i in batch_items])
        for item, judgement in zip(batch_items, judgements):
            if judgement.get("real_risk") is not False:
                confirmed.append(item)
    except Exception:
        # Fallback: evaluate individually or keep rule-based candidates if offline
        for item in batch_items:
            try:
                judgement = judge_snippet(item.get("evidence", ""))
                if judgement.get("real_risk") is not False:
                    confirmed.append(item)
            except Exception:
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
