"""FastAPI interface. Start with: uvicorn analysis.api:app --reload"""
import os, tempfile
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from analysis.analyze import analyze
from analysis.pdf_reader import read_pdf
from analysis.qa import answer_question

app = FastAPI(title="Financial Document Intelligence API", version="1.0.0", description="PDF financial statement analysis and page-grounded Q&A")
@app.get("/health")
def health(): return {"status": "ok", "service": "financial-document-intelligence"}
async def _save_pdf(upload):
    if not upload.filename or not upload.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Upload a PDF file.")
    data = await upload.read()
    if not data or len(data) > 30 * 1024 * 1024: raise HTTPException(status_code=400, detail="PDF is empty or exceeds 30 MB.")
    fd, path = tempfile.mkstemp(suffix=".pdf")
    with os.fdopen(fd, "wb") as f: f.write(data)
    return path
@app.post("/analyze")
async def analyze_endpoint(file: UploadFile = File(...), basis: str = Form(...)):
    path = await _save_pdf(file)
    try: return analyze(path, basis=basis, doc_name=file.filename).model_dump()
    except ValueError as exc: raise HTTPException(status_code=422, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail="Analysis failed unexpectedly. Check the server log and verify that the PDF is readable.")
    finally: os.unlink(path)
@app.post("/ask")
async def ask_endpoint(file: UploadFile = File(...), question: str = Form(...)):
    if not question.strip(): raise HTTPException(status_code=400, detail="Question cannot be empty.")
    path = await _save_pdf(file)
    try: return answer_question(read_pdf(path), question)
    except ValueError as exc: raise HTTPException(status_code=422, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail="Question answering failed unexpectedly. Verify that the PDF is readable.")
    finally: os.unlink(path)
