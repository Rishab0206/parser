from app.workers.celery_app import celery
from app.core.database import SessionLocal
from app.services.statement_processor import process_statement_pipeline
from app.core.logging import logger

@celery.task(bind=True, name="app.workers.parse_task.parse_statement_async")
def parse_statement_async(self, statement_id: str, pdf_password: str = None):
    logger.info(f"Starting Celery async parse task for statement {statement_id}")
    db = SessionLocal()
    try:
        result = process_statement_pipeline(statement_id, db, pdf_password)
        logger.info(f"Async parse completed successfully: {result}")
        return result
    except Exception as e:
        logger.error(f"Async parse failed for statement {statement_id}: {e}", exc_info=True)
        raise e
    finally:
        db.close()

