import time
from analysis.pdf_reader import read_pdf
from analysis.pipeline import confirm_risks, risk_score

pages = read_pdf("sample_report.pdf")

start = time.time()
candidates, confirmed = confirm_risks(pages)
minutes = round((time.time() - start) / 60, 1)

print("Keyword candidates:", len(candidates))
print("Confirmed by AI:", len(confirmed))
print("AI time:", minutes, "minutes")
print("Risk score (0-100):", risk_score(confirmed))

for f in confirmed:
    print("---", f["type"], "| page", f["page"])
    print(f["evidence"][:200])
