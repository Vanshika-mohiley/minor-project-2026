RISK_WORDS = {
    "going concern": "high",
    "material weakness": "high",
    "restatement": "high",
    "qualified opinion": "high",
    "fraud": "high",
    "litigation": "medium",
    "impairment": "medium",
    "penalty": "medium",
    "default": "medium",
    "cyber": "low",
}

SAFE_PHRASES = [
    "going concern basis",
    "impacting the going concern",
    "prevention and detection of fraud",
    "preventing and detecting fraud",
    "detecting fraud",
    "not reported any instance of fraud",
    "actual or suspected fraud",
    "whether due to fraud or error",
    "due to fraud or error",
    "no significant deficiencies",
    "no material weakness",
    "not identified any material weakness",
    "no fraud",
    "if we conclude that a material uncertainty exists",
]


def is_safe(snippet):
    low = snippet.lower()
    for phrase in SAFE_PHRASES:
        if phrase in low:
            return True
    return False


def find_risks(pages):
    flags = []
    for p in pages:
        text = p["text"]
        low = text.lower()
        for word, severity in RISK_WORDS.items():
            position = low.find(word)
            while position != -1:
                start = max(0, position - 80)
                snippet = text[start:position + 200]
                snippet = " ".join(snippet.split())
                if not is_safe(snippet):
                    flags.append({
                        "type": word,
                        "severity": severity,
                        "page": p["page"],
                        "evidence": snippet,
                    })
                position = low.find(word, position + len(word))
    return flags
