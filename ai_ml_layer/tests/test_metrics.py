from analysis.pdf_reader import read_pdf
from analysis.metrics import extract_metrics, change_percent

pages = read_pdf("sample_report.pdf")
m = extract_metrics(pages)

print("===== FINANCIAL SNAPSHOT =====")
for name, d in m.items():
    if d is None:
        print(name, ": NOT FOUND")
    else:
        print(name, ":", int(d["this_year"]), "| last year:", int(d["last_year"]), "| page", d["page"])

income = m["Total income"]
profit = m["Profit for the year"]
assets = m["Total assets"]
equity = m["Total equity"]

if income and profit and assets and equity:
    print()
    print("===== CALCULATED BY PYTHON =====")

    g = change_percent(income["this_year"], income["last_year"])
    print("Income growth:", round(g, 1), "%")
    print("  -> Total income grew by this much compared to last year.")

    pg = change_percent(profit["this_year"], profit["last_year"])
    print("Profit growth:", round(pg, 1), "%")
    print("  -> Profit grew by this much compared to last year.")

    margin = profit["this_year"] / income["this_year"] * 100
    print("Profit margin:", round(margin, 1), "%")
    print("  -> Out of every 100 rupees earned, this much was kept as profit.")

    eq_ratio = equity["this_year"] / assets["this_year"] * 100
    print("Equity / Assets:", round(eq_ratio, 1), "%")
    print("  -> This share of company assets is owned by shareholders.")
    print("     (The rest is owed to others. Higher means safer.)")
