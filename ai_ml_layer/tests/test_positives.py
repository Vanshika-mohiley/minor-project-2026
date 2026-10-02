from analysis.judge import judge_snippet

cases = [
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

correct = 0
for expected, text in cases:
    result = judge_snippet(text)
    ok = result["real_risk"] == expected
    if ok:
        correct = correct + 1
    mark = "OK   " if ok else "WRONG"
    print(mark, "| expected", expected, "| AI said", result["real_risk"], "|", text[:60])

print("Correct:", correct, "of", len(cases))
