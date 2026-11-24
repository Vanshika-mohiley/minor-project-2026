import sys
import analysis.judge as judge
from analysis.pdf_reader import read_pdf
from analysis.risk import find_risks

START = 1

if len(sys.argv) > 1:
    judge.MODEL = sys.argv[1]

pages = read_pdf("sample_report.pdf")

candidates = []
for f in find_risks(pages):
    if f["severity"] != "low":
        candidates.append(f)

step = max(1, len(candidates) // 20)
chosen = candidates[START::step][:20]

print("Model:", judge.MODEL)
print("Candidates:", len(candidates), "| judging:", len(chosen))

for number, f in enumerate(chosen, start=1):
    result = judge.judge_snippet(f["evidence"])
    print()
    print(number, "|", f["type"], "| page", f["page"], "| AI:", result["real_risk"])
    print("   ", f["evidence"][:220])
