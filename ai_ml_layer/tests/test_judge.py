import time
from analysis.judge import judge_snippet

samples = [
    ("Standard line (page 43)",
     "They have prepared the annual accounts on a going concern basis."),
    ("Standard line (page 198)",
     "future events or conditions may cause the Company to cease to continue as a going concern."),
    ("MADE-UP real risk 1",
     "The Company has defaulted on repayment of its bank loan and the lenders have issued a recall notice for the full amount."),
    ("MADE-UP real risk 2",
     "The auditor has issued a qualified opinion because the Company did not record a large impairment on its acquisitions."),
]

for label, text in samples:
    start = time.time()
    result = judge_snippet(text)
    seconds = round(time.time() - start, 1)
    print(label)
    print("  real_risk:", result["real_risk"], "|", seconds, "seconds")
    print("  reason:", result["reason"])
