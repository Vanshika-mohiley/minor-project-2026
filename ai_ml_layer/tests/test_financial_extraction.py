from analysis.metrics import extract_metrics, change_percent, to_number, detect_metadata, detected_basis


def test_indian_and_western_number_formats():
    assert to_number("10,22,401") == 1022401
    assert to_number("1,23,45,678") == 12345678
    assert to_number("1,234,567") == 1234567
    assert to_number("(15,124)") == -15124
    assert to_number("-") is None


def test_ril_style_standalone_statement_pages():
    pages = [
        {"page": 7, "text": "STANDALONE FINANCIAL STATEMENTS\nBalance Sheet\nTotal Assets\n10,22,401\n9,59,643\nTotal Equity\n5,43,087\n5,15,096"},
        {"page": 8, "text": "STANDALONE FINANCIAL STATEMENTS\nStatement of Profit and Loss\nTotal Income\n5,48,886\n5,60,070\nProfit for the Year\n35,262\n42,042"},
    ]
    result = extract_metrics(pages, "Standalone")
    assert result["Total income"]["this_year"] == 548886
    assert result["Profit for the year"]["this_year"] == 35262
    assert result["Total assets"]["this_year"] == 1022401
    assert result["Total equity"]["this_year"] == 543087


def test_us_10k_style_consolidated_statements():
    pages = [
        {"page": 7, "text": "CONSOLIDATED STATEMENTS OF OPERATIONS\nRevenue\n125,000 118,000\nNet income\n18,500 16,200"},
        {"page": 8, "text": "CONSOLIDATED BALANCE SHEETS\nTotal assets\n450,000 420,000\nTotal stockholders' equity\n210,000 195,000"},
    ]
    result = extract_metrics(pages, "Standalone")  # only consolidated basis exists
    assert detected_basis(pages, "Standalone") == "Consolidated"
    assert result["Total income"]["this_year"] == 125000
    assert result["Profit for the year"]["this_year"] == 18500
    assert result["Total assets"]["this_year"] == 450000
    assert result["Total equity"]["this_year"] == 210000


def test_selected_basis_not_mixed():
    pages = [
        {"page": 1, "text": "STANDALONE FINANCIAL STATEMENTS\nStatement of Profit and Loss\nTotal income\n100\n90\nProfit for the year\n10\n9"},
        {"page": 2, "text": "CONSOLIDATED FINANCIAL STATEMENTS\nStatement of Profit and Loss\nTotal income\n500\n450\nProfit for the year\n50\n45"},
    ]
    assert extract_metrics(pages, "Standalone")["Total income"]["this_year"] == 100
    assert extract_metrics(pages, "Consolidated")["Total income"]["this_year"] == 500


def test_statement_heading_and_table_can_be_split():
    pages = [
        {"page": 3, "text": "CONSOLIDATED STATEMENTS OF OPERATIONS"},
        {"page": 4, "text": "Revenue\n125,000 118,000\nNet income\n18,500 16,200"},
        {"page": 5, "text": "Other information"},
    ]
    assert extract_metrics(pages, "Consolidated")["Total income"]["this_year"] == 125000


def test_auditor_narrative_is_not_treated_as_a_statement_table():
    pages = [
        {"page": 1, "text": "Auditor report\nThe statements include total assets of 999 and revenue of 888, as described in the notes."},
    ]
    result = extract_metrics(pages, "Standalone")
    assert all(value is None for value in result.values())


def test_growth_handles_negative_values_and_zero():
    assert round(change_percent(80, 100), 1) == -20.0
    assert change_percent(100, 0) is None
