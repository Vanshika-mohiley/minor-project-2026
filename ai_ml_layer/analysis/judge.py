import json
import ollama

MODEL = "llama3.2:3b"

PROMPT = """You are a financial risk analyst. Read one sentence from a company's annual report.

Answer true if the sentence reports an actual adverse event or problem (for example: a penalty or fine, a lost customer, a restatement, a lawsuit, a negative audit opinion, a missed payment). If you are unsure, answer true.
Answer false if it is only a standard legal line, a general list of possible risks, or a statement that everything is fine.

Examples:
Sentence: "The regulator imposed a penalty of Rs 500 crore on the Company for violating norms."
{{"real_risk": true, "reason": "A penalty was actually imposed."}}
Sentence: "The Company has restated its previous year's results due to errors."
{{"real_risk": true, "reason": "Results were restated because of errors."}}
Sentence: "The Board is responsible for preventing and detecting fraud."
{{"real_risk": false, "reason": "Standard statement of responsibility."}}
Sentence: "Risks such as fraud and cyber-attacks may affect businesses in general."
{{"real_risk": false, "reason": "General list of possible risks."}}

Now judge this sentence.
Sentence: "{snippet}"
Reply ONLY with JSON in the same format."""


def judge_snippet(snippet):
    response = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": PROMPT.format(snippet=snippet)}],
        format="json",
        options={"temperature": 0, "num_predict": 80},
    )
    text = response["message"]["content"]
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return {"real_risk": None, "reason": "Could not read model answer"}

    value = data.get("real_risk")
    if isinstance(value, str):
        value = value.strip().lower() == "true"
    return {"real_risk": value, "reason": str(data.get("reason", ""))}
