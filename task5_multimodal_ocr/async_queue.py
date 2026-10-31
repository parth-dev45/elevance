"""
Task 5: Asynchronous Background Processing Queue.
Moves requests exceeding 30 seconds into a background queue and immediately notifies the customer.
"""
from typing import Dict, Any, Optional
from datetime import datetime
import uuid
from pydantic import BaseModel
from core.time_engine import time_engine
from core.config import config
from core.logger import audit_logger

class AsyncOCRJob(BaseModel):
    job_id: str
    file_path: str
    customer_message: str
    status: str = "QUEUED" # QUEUED, PROCESSING, COMPLETED, FAILED
    created_at: datetime
    simulated_duration_seconds: float
    customer_notification: str
    result: Optional[Dict[str, Any]] = None

class AsyncQueueManager:
    def __init__(self):
        self.jobs: Dict[str, AsyncOCRJob] = {}

    def dispatch_or_queue(self, file_path: str, customer_message: str,
                          processing_time_seconds: float = 2.0) -> Dict[str, Any]:
        """
        Evaluates processing time against 30-second threshold.
        If > 30 seconds: moves to background queue and returns notification for customer.
        Otherwise executes synchronously.
        """
        threshold = config.async_processing_threshold_seconds # 30 seconds

        if processing_time_seconds > threshold:
            job_id = f"ASYNC-OCR-{uuid.uuid4().hex[:6].upper()}"
            notification = (
                f"Your file requires in-depth optical processing that exceeds our 30-second immediate window "
                f"(estimated time: {round(processing_time_seconds, 1)}s). We have moved your request to our "
                f"secure background queue (Job ID: {job_id}). You will receive an instant notification once complete."
            )

            job = AsyncOCRJob(
                job_id=job_id,
                file_path=file_path,
                customer_message=customer_message,
                status="QUEUED",
                created_at=time_engine.now(),
                simulated_duration_seconds=processing_time_seconds,
                customer_notification=notification
            )
            self.jobs[job_id] = job
            audit_logger.log("WARNING", f"Processing exceeded 30s threshold ({processing_time_seconds}s). Job '{job_id}' queued in background.")

            return {
                "is_async": True,
                "job_id": job_id,
                "status": "QUEUED_BACKGROUND",
                "customer_notification": notification,
                "estimated_seconds": processing_time_seconds
            }

        return {
            "is_async": False,
            "status": "SYNC_PROCESSED",
            "duration_seconds": processing_time_seconds
        }

    def complete_job(self, job_id: str, result_data: Dict[str, Any]):
        """Marks background job as completed."""
        if job_id in self.jobs:
            self.jobs[job_id].status = "COMPLETED"
            self.jobs[job_id].result = result_data
            audit_logger.log("INFO", f"Async background job '{job_id}' successfully completed.")

async_queue_manager = AsyncQueueManager()
