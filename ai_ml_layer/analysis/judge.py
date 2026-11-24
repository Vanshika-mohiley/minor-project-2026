"""Optional local Ollama risk classifier. Deterministic fallback is handled by pipeline."""
import json
try:
    import ollama
except ImportError:  # Ollama is optional for offline/basic mode
    ollama = None

MODEL = "llama3.2:3b"
PROMPT = '''Classify whether the excerpt reports an actual adverse event that has happened or is happening to the company. Return JSON only: {"real_risk": true|false, "reason": "short explanation"}. Mark false for hypothetical risks, policy disclosures, standard audit wording, or explicit denials. Excerpt: {snippet}'''

def judge_snippet(snippet):
    if ollama is None:
        return {"real_risk": None, "reason": "Ollama package is not installed"}
    response = ollama.chat(model=MODEL, messages=[{"role": "user", "content": PROMPT.format(snippet=str(snippet)[:1800])}], format="json", options={"temperature": 0, "num_predict": 100})
    data = json.loads(response["message"]["content"])
    value = data.get("real_risk")
    if isinstance(value, str):
        value = value.strip().lower() == "true" if value.strip().lower() in {"true", "false"} else None
    if not isinstance(value, bool):
        value = None
    return {"real_risk": value, "reason": str(data.get("reason", ""))}
