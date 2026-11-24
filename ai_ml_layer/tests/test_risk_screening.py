from analysis.risk import find_risks
from analysis.pipeline import risk_score


def test_generic_audit_boilerplate_does_not_trigger_going_concern_flag():
    pages = [{"page": 12, "text": "The auditor evaluates management's use of the going concern basis and whether a material uncertainty exists that may cast significant doubt on the Company's ability to continue as a going concern."}]
    assert find_risks(pages) == []


def test_explicit_debt_default_is_flagged():
    pages = [{"page": 8, "text": "The company defaulted in repayment of a term loan during the reporting period."}]
    flags = find_risks(pages)
    assert len(flags) == 1
    assert flags[0]["type"] == "debt repayment default"
    assert flags[0]["page"] == 8


def test_explicit_denial_is_not_flagged():
    pages = [{"page": 4, "text": "There was no default in repayment of any loan during the year."}]
    assert find_risks(pages) == []


def test_repeated_mentions_do_not_saturate_score():
    flags = [{"type": "debt repayment default", "severity": "high"}] * 20
    assert risk_score(flags) == 20


def test_distinct_categories_add_but_do_not_overcount_repeats():
    flags = [
        {"type": "debt repayment default", "severity": "high"},
        {"type": "debt repayment default", "severity": "high"},
        {"type": "regulatory penalty", "severity": "medium"},
    ]
    assert risk_score(flags) == 30


def test_no_flags_means_no_detected_signals_not_no_risk():
    assert risk_score([]) == 0


def test_routine_contingent_liability_claim_is_not_automatically_scored():
    pages = [{
        "page": 262,
        "text": "Claims against the Company, not acknowledged as debts, amounted to INR 1,944 crore.",
    }]
    assert find_risks(pages) == []
