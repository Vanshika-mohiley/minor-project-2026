import json
import ollama

MODEL = "llama3.2:3b"

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
