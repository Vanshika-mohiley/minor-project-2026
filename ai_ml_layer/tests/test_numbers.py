from analysis.pdf_reader import read_pdf

pages = read_pdf("sample_report.pdf")


def count_number_cells(table):
    count = 0
    for row in table:
        for cell in row:
            if cell:
                cleaned = cell.replace(",", "").replace(".", "")
                cleaned = cleaned.replace("(", "").replace(")", "")
                if cleaned.strip().isdigit():
                    count = count + 1
    return count


best_page = None
best_score = 0
best_table = []

for p in pages:
    for table in p["tables"]:
        score = count_number_cells(table)
        if score > best_score:
            best_score = score
            best_page = p["page"]
            best_table = table

print("Best number-table is on page", best_page, "with", best_score, "number cells")
for row in best_table[:8]:
    print(row)
