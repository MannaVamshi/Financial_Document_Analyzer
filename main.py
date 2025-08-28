# main.py
import uuid, os
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from sqlalchemy.orm import Session
from db import SessionLocal, engine
from models import Base, Document, AnalysisResult
from worker_tasks import process_document  # directly called now

# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Financial Document Analyzer")

UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Dependency for DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/analyze")
async def analyze(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    uid = str(uuid.uuid4())
    dest = os.path.join(UPLOAD_DIR, f"{uid}.pdf")
    content = await file.read()
    with open(dest, "wb") as f:
        f.write(content)

    # Save document in DB
    doc = Document(filename=file.filename, path=dest)
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Generate unique task_id for this analysis
    task_uuid = str(uuid.uuid4())

    # Run task synchronously (no Celery/Redis needed)
    try:
        result = process_document(doc.id, dest)  # direct call
        status = "SUCCESS"
        error = None
    except Exception as e:
        result = None
        status = "FAILED"
        error = str(e)

    # Store AnalysisResult in DB
    ar = AnalysisResult(
        document_id=doc.id,
        task_id=task_uuid,  # unique per document
        status=status,
        result=result,
        error=error
    )
    db.add(ar)
    db.commit()
    db.refresh(ar)

    return {
        "task_id": ar.task_id,
        "document_id": doc.id,
        "status": ar.status,
        "result": ar.result,
        "error": ar.error
    }

@app.get("/status/{task_id}")
def get_status(task_id: str, db: Session = Depends(get_db)):
    ar = db.query(AnalysisResult).filter(AnalysisResult.task_id == task_id).first()
    if not ar:
        raise HTTPException(status_code=404, detail="Task not found")

    return {
        "task_id": ar.task_id,
        "document_id": ar.document_id,
        "status": ar.status,
        "result": ar.result,
        "error": ar.error
    }
