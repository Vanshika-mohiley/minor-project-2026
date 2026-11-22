import json
import os
import urllib.request

CLOUD_MODEL = os.getenv("LLM_MODEL", "llama-3.1-8b-instant")
LOCAL_MODEL = "llama3.2:3b"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

PROMPT = """You are a financial risk analyst. Read one sentence from a company's annual report.

Answer true ONLY if the sentence says that something bad HAS ALREADY happened or IS happening to the company (for example: a penalty or fine was imposed, a customer was lost, results were restated, a lawsuit was filed, the auditor gave a negative opinion, a payment was missed).
Answer false if the sentence only says that something MAY, COULD or CAN happen, or if it is an accounting policy, an audit procedure, a standard legal line, a general list of possible risks, or a statement that everything is fine.

Examples:
Sentence: "The regulator imposed a penalty of Rs 500 crore on the Company for violating norms."
{{"real_risk": true, "reason": "A penalty was actually imposed."}}
Sentence: "The Company has restated its previous year's results due to errors."
{{"real_risk": true, "reason": "Results were restated because of errors."}}
Sentence: "The Board is responsible for preventing and detecting fraud."
{{"real_risk": false, "reason": "Standard statement of responsibility."}}
Sentence: "Risks such as fraud and cyber-attacks may affect businesses in general."
{{"real_risk": false, "reason": "General list of possible risks."}}
Sentence: "Errors in reporting may occur and may not always be detected."
{{"real_risk": false, "reason": "Only says something may happen."}}
Sentence: "Goodwill is tested for impairment when its value may not be recoverable."
{{"real_risk": false, "reason": "Accounting policy."}}

Now judge this sentence.
Sentence: "{snippet}"
Reply ONLY with JSON in the same format."""

BATCH_PROMPT = """You are a financial risk analyst. Judge each numbered snippet from an annual report.
Set "real_risk": true ONLY if something bad HAS ALREADY happened or IS happening to the company (penalty imposed, lawsuit filed, restatement, missed payment, negative audit opinion).
Set "real_risk": false if it is hypothetical ("may", "could"), standard policy, or general risk disclosure.

Snippets:
{numbered_snippets}

Reply ONLY with a JSON object mapping each string ID ("0", "1", ...) to {{"real_risk": true/false, "reason": "short reason"}}."""


def _call_llm(prompt_text, json_mode=True, max_tokens=150):
    """Production router: Cloud Groq API first (zero user setup), local Ollama second."""
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if api_key:
        payload = {
            "model": CLOUD_MODEL,
            "messages": [{"role": "user", "content": prompt_text}],
            "temperature": 0,
            "max_tokens": max_tokens,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        req = urllib.request.Request(
            GROQ_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "FinSight-AI/1.0",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return body["choices"][0]["message"]["content"]

    import ollama
    response = ollama.chat(
        model=LOCAL_MODEL,
        messages=[{"role": "user", "content": prompt_text}],
        format="json" if json_mode else None,
        options={"temperature": 0, "num_predict": max_tokens},
    )
    return response["message"]["content"]


def judge_snippet(snippet):
    text = _call_llm(PROMPT.format(snippet=snippet), json_mode=True, max_tokens=80)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return {"real_risk": None, "reason": "Could not read model answer"}

    value = data.get("real_risk")
    if isinstance(value, str):
        value = value.strip().lower() == "true"
    return {"real_risk": value, "reason": str(data.get("reason", ""))}


def judge_snippets_batch(snippets):
    """Evaluates all candidate snippets in ONE single LLM call for 15x faster throughput."""
    if not snippets:
        return []
    numbered = "\n".join(f'[{i}] "{s[:350]}"' for i, s in enumerate(snippets))
    text = _call_llm(
        BATCH_PROMPT.format(numbered_snippets=numbered),
        json_mode=True,
        max_tokens=min(1200, 70 * len(snippets) + 60),
    )
    data = json.loads(text)
    results = []
    for i in range(len(snippets)):
        entry = data.get(str(i), {})
        val = entry.get("real_risk")
        if isinstance(val, str):
            val = val.strip().lower() == "true"
        results.append({"real_risk": val, "reason": str(entry.get("reason", ""))})
    return results
