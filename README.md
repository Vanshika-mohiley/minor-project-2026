# FinSight AI — Corporate Filing Intelligence

FinSight AI is an academic prototype for extracting selected financial metrics and risk-related disclosures from company annual reports and SEC 10-K style PDFs.

## Run on Ubuntu / Linux

```bash
unzip FinSight_AI_Presentation_Ready.zip
cd minor-project-2026
chmod +x run_dashboard.sh
./run_dashboard.sh
```

Open the local URL printed by Streamlit (normally http://localhost:8501). The dashboard starts without sample figures. Results appear only after a PDF is uploaded and a statement basis is selected.

For the API, open a second terminal in the project folder:

```bash
chmod +x run_api.sh
./run_api.sh
```

API documentation: http://127.0.0.1:8000/docs

## What is supported

- Page-by-page selectable PDF text extraction, with optional Tesseract OCR fallback for image-only pages.
- Standalone and consolidated statement title detection, with a fallback to the only statement basis actually present.
- Common statement titles including Statement of Profit and Loss, Income Statement, Statements of Operations, Balance Sheet and Statement of Financial Position.
- Common row labels for total income/revenue, profit/net income, total assets and total equity/shareholders' equity.
- Indian and western comma grouping, decimal amounts and bracketed negatives.
- Source PDF page numbers and the matched source row label for each extracted metric.
- Growth, profit margin and equity-to-assets calculations only when source values are available.
- Rule-based event disclosure screening, with evidence excerpts and page references.
- Page-grounded keyword retrieval for report Q&A.


## Regression checks performed on this build

- The bundled Infosys FY2025-26 annual-report PDF is tested through both Standalone and Consolidated analysis paths, including company, period, INR-crore units, four financial metrics, source pages and the risk index.
- A separate local regression run was performed against Reliance Industries Integrated Annual Report 2024-25, for both Standalone and Consolidated statements.
- The FastAPI `/health` and `/analyze` upload routes are covered by automated tests. The packaged Infosys report is uploaded through `/analyze` as an end-to-end backend test.
- Risk scoring is category-based: repeated occurrences of the same category do not add more points. Routine contingent-liability wording and standard audit boilerplate are not scored automatically.

From the project root, run the tests with:

```bash
cd ai_ml_layer
PYTHONPATH=. python -m pytest -q
```

## Risk index explanation

The 0–100 dial is a **disclosure signal index**, not a probability of failure, credit rating, investment recommendation or audit opinion. It adds transparent points for distinct event-like disclosure categories, with repeated mentions in one category counted once. Generic risk-factor wording and standard audit boilerplate are not scored. A zero means the rules did not find a qualifying passage, not that the company has no risk. All flagged passages require human review.

## Verify before relying on results

Financial reports differ in layout, terminology, reporting standards and units. The extractor intentionally leaves uncertain figures blank instead of guessing. It does not convert currencies or units. Always compare the displayed value, source row and PDF page against the audited report. Scanned tables, rotated pages, complex multi-column layouts and restated periods may require manual review. This is a college prototype, not an audited accounting system.

## Tests

From `ai_ml_layer`:

```bash
PYTHONPATH=. python -m pytest -q
```

To run the real-report regression check after extracting the ZIP, point `FINSIGHT_TEST_PDF` to a local annual-report PDF:

```bash
FINSIGHT_TEST_PDF=/path/to/annual-report.pdf PYTHONPATH=. python -m pytest -q tests/test_real_pdf_optional.py
```
