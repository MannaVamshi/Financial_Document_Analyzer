# worker_tasks.py
from celery_app import celery
from task import analyze_financial_document  # your analysis function
from db import SessionLocal
from models import AnalysisResult
import traceback
import json

@celery.task(bind=True)
def process_document(self, document_id: int, file_path: str):
    """
    Celery task that runs the analysis and saves results to DB.
    Returns: dict result
    """
    db = SessionLocal()
    task_id = self.request.id
    # Create or update AnalysisResult row with PENDING/STARTED
    try:
        ar = AnalysisResult(
            document_id=document_id,
            task_id=task_id,
            status="STARTED",
            result=None,
            error=None,
        )
        db.add(ar)
        db.commit()
        db.refresh(ar)

        # Run the analysis (this calls your analyze_financial_document)
        result = analyze_financial_document(file_path)

        # Save result
        ar.status = "SUCCESS"
        ar.result = result
        db.add(ar)
        db.commit()
        return {"status": "SUCCESS", "result": result}
    except Exception as exc:
        db.rollback()
        tb = traceback.format_exc()
        # find the existing analysis record by task_id and update
        ar = db.query(AnalysisResult).filter(AnalysisResult.task_id == task_id).first()
        if ar:
            ar.status = "FAILURE"
            ar.error = str(exc) + "\n" + tb
            db.add(ar)
            db.commit()
        return {"status": "FAILURE", "error": str(exc)}
    finally:
        db.close()
