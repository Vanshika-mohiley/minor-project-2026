"""Conservative disclosure screening; findings are signals for human review."""
from __future__ import annotations
import re

# Only event-like disclosures are scored. Generic words such as 'risk', 'fraud',
# 'litigation' in policy headings, and going-concern boilerplate are not enough.
RULES = [
    ("modified audit opinion", "high", re.compile(r"\b(?:qualified|adverse)\s+opinion\b|\bdisclaimer\s+of\s+opinion\b", re.I)),
    ("going-concern uncertainty", "high", re.compile(r"(?:material uncertainty|significant doubt|substantial doubt).{0,140}(?:going concern|ability to continue)|(?:going concern|ability to continue).{0,140}(?:material uncertainty|significant doubt|substantial doubt)", re.I | re.S)),
    ("debt repayment default", "high", re.compile(r"\b(?:default(?:ed)?\s+(?:in|on)\s+(?:repayment|payment|loan|interest)|failure to repay|failed to (?:repay|pay)|breach of (?:a\s+)?financial covenants?)\b", re.I)),
    ("fraud finding", "high", re.compile(r"\b(?:fraud was detected|fraud has been detected|fraud has been identified|confirmed fraud|fraudulent transactions? (?:was|were|has been) identified|instances? of fraud (?:was|were) reported)\b", re.I)),
    ("material weakness in controls", "high", re.compile(r"\b(?:identified|reported|disclosed|there is|exists?)\b.{0,55}\bmaterial weakness\b.{0,70}\b(?:internal control|financial reporting)\b", re.I)),
    ("financial restatement", "high", re.compile(r"\b(?:restated|restatement of)\s+(?:the\s+)?(?:financial statements|financial results|accounts)\b", re.I)),
    ("regulatory penalty", "medium", re.compile(r"\b(?:(?:a\s+)?(?:penalty|fine)\s+(?:of\s+)?(?:₹|\$|INR|USD)?\s*[\d,]+\s+(?:was\s+)?(?:imposed|levied)|(?:imposed|levied)\s+(?:a\s+)?(?:penalty|fine))\b", re.I)),
    ("material litigation", "medium", re.compile(r"\b(?:material|significant|pending|ongoing)\s+(?:legal\s+)?(?:litigation|proceedings?|claims?)\b", re.I)),
]

_NEGATION = re.compile(r"\b(?:no|not|never|without|neither|did not|does not|has not|have not|had not|not been)\b", re.I)
_BOILERPLATE = re.compile(
    r"whether due to fraud or error|prevention and detection of fraud|going concern basis of accounting|"
    r"management's assessment of going concern|risk of material misstatement|"
    r"whether a material uncertainty exists related to events or conditions that may cast significant doubt|"
    r"our conclusions are based on the audit evidence obtained|"
    r"we are required to draw attention to the related disclosures",
    re.I,
)
_HYPOTHETICAL = re.compile(r"\b(?:may|might|could|would|potential|possible|if|in the event of)\b", re.I)


def _sentences(text: str):
    # PDF extraction commonly inserts a newline after every visual line, even
    # in the middle of a sentence. Join those lines before sentence splitting
    # so negation and audit-boilerplate context is not lost.
    normalized = re.sub(r"\s+", " ", str(text or "")).strip()
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", normalized) if s.strip()]


def find_risks(pages):
    findings = []
    seen = set()
    for page in pages:
        text = str(page.get("text", ""))
        for sentence in _sentences(text):
            compact = " ".join(sentence.split())
            if not compact or _BOILERPLATE.search(compact):
                continue
            for label, severity, pattern in RULES:
                match = pattern.search(compact)
                if not match:
                    continue
                prefix = compact[max(0, match.start() - 100):match.start()]
                # Negations close to the trigger and forward-looking risk language
                # are not counted as actual adverse events.
                if _NEGATION.search(prefix[-70:]) or _HYPOTHETICAL.search(compact):
                    continue
                # One displayed flag per category per PDF page. Multiple nearby
                # matches on the same page should not inflate the gauge or UI.
                key = (label, page.get("page", 1))
                if key in seen:
                    continue
                seen.add(key)
                findings.append({
                    "type": label,
                    "severity": severity,
                    "page": int(page.get("page", 1)),
                    "evidence": compact[:600],
                    "review_status": "human_review_required",
                })
    return findings
