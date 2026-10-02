import sys
from analysis.pdf_reader import read_pdf
from analysis.metrics import to_number, change_percent, extract_metrics
from analysis.risk import find_risks
from analysis.pipeline import risk_score
from analysis.judge import judge_snippet
from analysis.analyze import analyze
from analysis.schemas import AnalysisReport

results = []
cache = {}


def run(name, func):
    try:
        ok = bool(func())
        print("PASS " if ok else "FAIL ", name)
    except Exception as error:
        ok = False
        print("FAIL ", name, "-> crashed:", error)
    results.append(ok)


def fake_page(text):
    return [{"page": 1, "text": text}]


def empty_report_ok():
    r = AnalysisReport(doc_id="x", summary="y")
    return r.risk_score == 0 and r.risk_flags == [] and r.metrics.total_income is None


print("--- A. Quick checks (no PDF, no AI) ---")
run("to_number reads 1,55,310", lambda: to_number("1,55,310") == 155310)
run("to_number reads (45) as negative", lambda: to_number("(45)") == -45)
run("to_number ignores a dash", lambda: to_number("–") is None)
run("income growth formula gives 9.9", lambda: round(change_percent(155310, 141374), 1) == 9.9)
run("profit growth formula gives 14.2", lambda: round(change_percent(29211, 25568), 1) == 14.2)
run("empty AnalysisReport has safe defaults", empty_report_ok)
run("standard going-concern line is NOT flagged",
    lambda: find_risks(fake_page("They have prepared the annual accounts on a going concern basis.")) == [])
run("a real default IS flagged",
    lambda: [f["type"] for f in find_risks(fake_page("The Company is in default on its bank loan and lenders have recalled the facility."))] == ["default"])
run("a normal sentence is not flagged",
    lambda: find_risks(fake_page("Revenue grew nicely this year.")) == [])
run("capital letters are still caught",
    lambda: len(find_risks(fake_page("GOING CONCERN doubt exists."))) == 1)
run("score of no flags is 0", lambda: risk_score([]) == 0)
run("same risk type counts at most twice", lambda: risk_score([{"type": "litigation"}] * 10) == 20)
run("score never goes above 100",
    lambda: risk_score([{"type": "going concern"}] * 3 + [{"type": "fraud"}] * 3 + [{"type": "material weakness"}]) == 100)


def get_pages():
    if "pages" not in cache:
        cache["pages"] = read_pdf("sample_report.pdf")
    return cache["pages"]


def get_metrics():
    if "metrics" not in cache:
        cache["metrics"] = extract_metrics(get_pages())
    return cache["metrics"]


EXPECTED = {
    "Total income": (155310, 141374),
    "Profit for the year": (29211, 25568),
    "Total assets": (126691, 124936),
    "Total equity": (80874, 87332),
}


def check_metric(name):
    d = get_metrics()[name]
    return d is not None and (d["this_year"], d["last_year"]) == EXPECTED[name]


def pages_with_text():
    count = 0
    for p in get_pages():
        if len(p["text"]) > 500:
            count = count + 1
    return count


def growth_matches_report():
    d = get_metrics()["Total income"]
    return round(change_percent(d["this_year"], d["last_year"]), 1) == 9.9


CASES = [
    (True, "During the year, the Company paid a penalty of Rs 120 crore to the tax authority for late filing of returns."),
    (True, "The Company lost its largest client, which contributed 22% of revenue, after the contract was terminated in March."),
    (True, "The statutory auditor has expressed an adverse opinion on the internal financial controls of the Company."),
    (True, "A class action lawsuit has been filed against the Company in a US court seeking damages of USD 300 million."),
    (True, "The Company has delayed payment of interest on its debentures for two consecutive quarters."),
    (True, "A cyber attack in November compromised customer data, and the Company had to pay a ransom to restore its systems."),
    (False, "There were no instances of fraud reported by the auditors during the year."),
    (False, "The Company has not received any notice of penalty from any regulator."),
    (False, "There has been no default in repayment of any loan during the year."),
]


def ai_cases():
    correct = 0
    for expected, text in CASES:
        if judge_snippet(text)["real_risk"] == expected:
            correct = correct + 1
    print("      AI got", correct, "of", len(CASES), "right")
    return correct >= 8


def get_report():
    if "report" not in cache:
        cache["report"] = analyze("sample_report.pdf")
    return cache["report"]


def flags_ok():
    for f in get_report().risk_flags:
        if f.page <= 0 or f.evidence == "":
            return False
    return True


def json_roundtrip():
    text = get_report().model_dump_json()
    return AnalysisReport.model_validate_json(text).doc_id == "sample_report.pdf"


if "--quick" not in sys.argv:
    print()
    print("--- B. Infosys PDF checks (about 1 minute) ---")
    run("PDF has more than 300 pages", lambda: len(get_pages()) > 300)
    run("more than 100 pages have real text", lambda: pages_with_text() > 100)
    run("Total income matches the report", lambda: check_metric("Total income"))
    run("Profit matches the report", lambda: check_metric("Profit for the year"))
    run("Total assets matches the report", lambda: check_metric("Total assets"))
    run("Total equity matches the report", lambda: check_metric("Total equity"))
    run("income growth = 9.9, same as the report says", growth_matches_report)

    print()
    print("--- C. AI judge checks (about 20 seconds) ---")
    run("AI judge gets at least 8 of 9 cases right", ai_cases)

if "--full" in sys.argv:
    print()
    print("--- D. Full analyze() run (about 5 minutes, please wait) ---")
    run("risk score is between 0 and 100", lambda: 0 <= get_report().risk_score <= 100)
    run("income growth in the JSON is 9.9", lambda: get_report().metrics.income_growth_pct == 9.9)
    run("every flag has a page and evidence", flags_ok)
    run("JSON can be saved and loaded back", json_roundtrip)

print()
print(sum(results), "of", len(results), "checks passed")
if sum(results) == len(results):
    print("ALL GOOD")
else:
    print("Some checks FAILED - copy this whole output and send it to me")
