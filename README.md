# FinSight AI — Financial Document Intelligence & Risk Screener

<p align="center">
  <strong>Turn long corporate reports into structured financial insights.</strong><br>
  Extract selected financial metrics, review disclosure signals with source-page evidence, and find relevant passages in annual reports.
</p>

<p align="center">
  <a href="https://minor-project-2026-cwh7njkikl8oxhg2qqvnj7.streamlit.app/">Live Demo</a> ·
  <a href="https://github.com/Vanshika-mohiley/minor-project-2026/issues">Report a bug / request a feature</a>
</p>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white">
  <img alt="Streamlit" src="https://img.shields.io/badge/UI-Streamlit-FF4B4B?logo=streamlit&logoColor=white">
  <img alt="FastAPI" src="https://img.shields.io/badge/API-FastAPI-009688?logo=fastapi&logoColor=white">
  <img alt="Platforms" src="https://img.shields.io/badge/OS-Windows%20%7C%20macOS%20%7C%20Linux-informational">
</p>

FinSight AI is an academic prototype for analysing corporate annual reports and SEC 10-K-style PDF documents. It combines PDF text extraction, conservative financial-statement parsing, deterministic financial calculations, rule-based disclosure screening, and page-grounded retrieval. It is designed to help a reviewer find useful figures and passages faster—not to replace an accountant, auditor, or investment professional.

> **Cross-platform:** The project is Python-based and includes local setup instructions for Windows, macOS, and Linux. The current development build was tested locally on Ubuntu with Python 3.14.4. The Windows and macOS instructions are provided for users, but those platforms have not yet been independently validated in CI.

## Contents

- [Live demo](#live-demo)
- [Features](#features)
- [How the analysis works](#how-the-analysis-works)
- [Technology stack](#technology-stack)
- [Requirements](#requirements)
- [Run locally](#run-locally)
  - [1. Clone the repository](#1-clone-the-repository)
  - [2. Windows — PowerShell](#2-windows--powershell)
  - [3. macOS](#3-macos)
  - [4. Linux](#4-linux)
- [Optional OCR setup](#optional-ocr-setup-for-scanned-pdfs)
- [Run the FastAPI backend](#run-the-fastapi-backend)
- [API endpoints](#api-endpoints)
- [Run tests](#run-tests)
- [Project structure](#project-structure)
- [Known limitations](#known-limitations)
- [Contributing](#contributing)

## Live demo

**[Open FinSight AI](https://minor-project-2026-cwh7njkikl8oxhg2qqvnj7.streamlit.app/)**

The dashboard does not load fabricated sample figures. Upload a PDF and choose a statement basis to analyse it. Do not upload confidential or sensitive documents to a public demo; use a local installation for private documents.

## Features

| Feature | What it does |
|---|---|
| PDF ingestion | Extracts selectable text page by page with PyMuPDF. Optional Tesseract OCR is used as a fallback for pages with little or no selectable text. |
| Statement basis | Looks for Standalone or Consolidated income-statement and balance-sheet pages, with a cautious fallback if only one basis is present. |
| Financial metrics | Attempts to extract total income/revenue, profit, total assets, and total equity, including comparative-period values and source-page references. |
| Financial calculations | Calculates available year-over-year growth, net profit margin, and equity-to-assets ratio from extracted values. |
| Disclosure screening | Finds selected event-like disclosure patterns and displays evidence excerpts, page numbers, and severity for human review. |
| Filing Q&A | Retrieves relevant passages from the uploaded report and shows their source PDF pages. |
| HTTP API | Provides health, financial-analysis, and question-answering endpoints through FastAPI. |

The extractor recognises common Indian and Western number-grouping formats and common financial-statement labels. It deliberately leaves uncertain values blank instead of guessing.

## How the analysis works

1. **Read the report.** PyMuPDF extracts text and page numbers. If a page has too little selectable text, the reader can attempt OCR when Tesseract is installed.
2. **Locate financial statements.** The parser looks for common income-statement and balance-sheet titles and identifies the requested reporting basis where possible.
3. **Extract selected metrics.** It searches statement rows for total income/revenue, profit, total assets, and total equity, retaining source labels and page references where available.
4. **Calculate derived values.** Growth and ratios are calculated from extracted values only. The system does not invent missing values or convert currencies/units.
5. **Screen disclosures.** Transparent rules identify selected event-like passages. The resulting 0–100 index is a disclosure triage signal, not a probability or credit score.
6. **Retrieve report passages.** The Q&A helper ranks relevant report text using keyword matching and returns page-grounded excerpts for review.

**AI/ML scope:** The default path is deterministic and rule-based. It does not require a hosted LLM to produce its financial metrics, summary, risk index, or Q&A response. The project includes an optional Ollama-related module/dependency, but the default analysis pipeline does not invoke an LLM. This README describes the behaviour of the current code rather than implying that every feature is deep-learning powered.

## Technology stack

- **Python** — application and analysis logic
- **PyMuPDF** — PDF text extraction
- **Pydantic** — structured analysis models
- **Streamlit** — interactive dashboard
- **Plotly** — financial charts
- **FastAPI + Uvicorn** — HTTP API
- **Pytesseract + Tesseract OCR** — optional OCR fallback for scanned pages
- **Pandas** — tabular data support
- **Pytest** — automated tests

## Requirements

- Python **3.11 or later**
- Git
- Internet access for the initial Python dependency installation
- Tesseract OCR only if you need OCR for scanned/image-only PDF pages

Run all commands below from a terminal. Unless a step says otherwise, start in the repository root—the directory containing `README.md`, `frontend/`, and `ai_ml_layer/`.

## Run locally

### 1. Clone the repository

To clone the default branch:

```bash
git clone https://github.com/Vanshika-mohiley/minor-project-2026.git
cd minor-project-2026
```

To try the latest development branch before it is merged into `main`:

```bash
git clone --branch feature/finsight-backend-fixes https://github.com/Vanshika-mohiley/minor-project-2026.git
cd minor-project-2026
```

### 2. Windows — PowerShell

Open PowerShell in the repository folder.

Create and activate a virtual environment, then install dependencies:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r ai_ml_layer\requirements.txt
```

If PowerShell blocks activation, allow it for the current terminal session and activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Start the dashboard:

```powershell
python -m streamlit run frontend/app.py
```

Open the local URL printed by Streamlit, usually **http://localhost:8501**.

### 3. macOS

Open Terminal in the repository folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r ai_ml_layer/requirements.txt
python -m streamlit run frontend/app.py
```

Open **http://localhost:8501**.

### 4. Linux

Open a terminal in the repository folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r ai_ml_layer/requirements.txt
python -m streamlit run frontend/app.py
```

Open **http://localhost:8501**.

The repository also includes `run_dashboard.sh` and `run_api.sh` convenience scripts for macOS/Linux shells. The direct Python commands above are the clearest cross-platform approach.

## Optional OCR setup for scanned PDFs

Selectable-text PDFs can be analysed without installing the Tesseract application. For image-only or scanned pages, install the Tesseract OCR engine and ensure the `tesseract` executable is available on your system `PATH`.

- **Windows:** Follow the [Tesseract installation guide](https://tesseract-ocr.github.io/tessdoc/Installation.html), then ensure the installation folder is on `PATH`.
- **macOS (Homebrew):** `brew install tesseract`
- **Ubuntu/Debian:** `sudo apt-get update && sudo apt-get install tesseract-ocr`

OCR can misread characters and numbers. Always verify OCR-derived figures against the original PDF page.

## Run the FastAPI backend

The Streamlit dashboard can run independently. To start the API as well, keep the dashboard running and open a **second terminal**.

Activate the virtual environment from the repository root first.

**Windows (PowerShell):**

```powershell
.\.venv\Scripts\Activate.ps1
Set-Location ai_ml_layer
python -m uvicorn analysis.api:app --host 127.0.0.1 --port 8000
```

**macOS / Linux:**

```bash
source .venv/bin/activate
cd ai_ml_layer
python -m uvicorn analysis.api:app --host 127.0.0.1 --port 8000
```

When the API is running:

- Health check: **http://127.0.0.1:8000/health**
- Interactive API documentation: **http://127.0.0.1:8000/docs**

Stop either local server with `Ctrl+C` in the terminal where it is running.

## API endpoints

| Method | Endpoint | Input | Purpose |
|---|---|---|---|
| `GET` | `/health` | — | Returns API health status. |
| `POST` | `/analyze` | Multipart PDF file and `basis` (`Standalone` or `Consolidated`) | Analyses the uploaded report and returns structured results. |
| `POST` | `/ask` | Multipart PDF file and `question` | Retrieves relevant report passages and their page references. |

The API currently accepts PDF uploads up to **30 MB** per request. The Streamlit dashboard has a separate **200 MB** upload check. Use `/docs` to inspect request schemas and try endpoints interactively.

## Run tests

Activate the virtual environment first. Then run the tests from inside `ai_ml_layer`.

**Windows (PowerShell):**

```powershell
Set-Location ai_ml_layer
$env:PYTHONPATH = "."
python -m pytest -q
```

**macOS / Linux:**

```bash
cd ai_ml_layer
PYTHONPATH=. python -m pytest -q
```

The current development branch was locally checked on Ubuntu / Python 3.14.4: **23 tests passed and 1 optional real-PDF test was skipped**. This is a record of that local run, not a claim that the test suite has been run on every operating system.

To run the optional real-report test with your own PDF, set `FINSIGHT_TEST_PDF` to the file path before running the test. For example:

```bash
FINSIGHT_TEST_PDF="/path/to/annual-report.pdf" PYTHONPATH=. python -m pytest -q tests/test_real_pdf_optional.py
```

## Project structure

```text
minor-project-2026/
├── ai_ml_layer/
│   ├── analysis/
│   │   ├── analyze.py       # Main document-analysis flow
│   │   ├── api.py           # FastAPI endpoints
│   │   ├── compare.py       # Multi-document comparison helper
│   │   ├── metrics.py      # Financial metric extraction
│   │   ├── pdf_reader.py   # PDF text extraction and OCR fallback
│   │   ├── qa.py           # Page-grounded report Q&A
│   │   ├── risk.py         # Disclosure-pattern screening
│   │   └── ...
│   ├── tests/
│   ├── requirements.txt
│   └── sample_report.pdf
├── frontend/
│   └── app.py               # Streamlit dashboard
├── run_api.sh               # macOS/Linux API helper
├── run_dashboard.sh         # macOS/Linux dashboard helper
└── README.md
```

## Known limitations

- **Academic prototype:** This project is for learning, demonstration, and decision-support experimentation. It is not an audited accounting system, credit rating, investment recommendation, or substitute for professional review.
- **Limited metric coverage:** The current extractor focuses on selected income-statement and balance-sheet metrics. It does not claim to understand every line item or every financial-reporting format.
- **Conservative extraction:** Reports vary in layout, terminology, units, and accounting standards. Uncertain values are left blank; currencies and units are not converted.
- **Disclosure signal index:** The 0–100 index is a rule-based disclosure triage score, not a probability of default, fraud, insolvency, or company failure. Repeated mentions in the same category are not intended to inflate the score. A zero score does not mean that a company has no risk.
- **Human verification:** Check every extracted figure, source row, page number, and flagged passage against the original audited report before relying on it.
- **PDF quality:** Upload an unlocked, readable PDF. Scanned, rotated, encrypted, or complex multi-column documents may require OCR or manual review.
- **Privacy:** Use a local installation for confidential reports. Upload documents to the public demo only if you are comfortable sharing them with that hosted service.
- **Operating-system coverage:** The Python setup is documented for Windows, macOS, and Linux, but only the Ubuntu development environment has been verified for this build so far.

## Contributing

Issues and pull requests are welcome.

1. Fork the repository.
2. Create a feature branch for your change.
3. Make the change and add or update tests where appropriate.
4. Run the test suite.
5. Open a pull request with a clear description and validation notes.

---

<p align="center">
  Built as an academic AI & ML project.<br>
  <a href="https://github.com/Vanshika-mohiley/minor-project-2026">FinSight AI on GitHub</a>
</p>
