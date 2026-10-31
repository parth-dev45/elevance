"""
Task 3: Maintenance Window Gatekeeper and Exponential Retry Scheduler.
Activates approved updates only during configured maintenance window (01:00 - 05:00).
Retries failed updates after 15, 30, and 60 minutes.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from core.time_engine import time_engine
from core.config import config
from core.logger import audit_logger
from core.security import UserRole, security_service
from task3_knowledge_pipeline.pipeline import kb_pipeline, KBDocument
from task3_knowledge_pipeline.quality_gate import quality_gate

class ScheduledUpdateJob(BaseModel):
    job_id: str
    scheduled_time: datetime
    doc_ids: List[str]
    attempt_count: int = 0
    max_retries: int = 3
    retry_delays_minutes: List[int] = Field(default_factory=lambda: [15, 30, 60])
    status: str = "SCHEDULED" # SCHEDULED, IN_PROGRESS, ACTIVE, FAILED, RETRYING, REJECTED
    failure_reason: Optional[str] = None
    last_attempt_time: Optional[datetime] = None

class KBScheduler:
    def __init__(self):
        self.jobs: Dict[str, ScheduledUpdateJob] = {}

    def schedule_update(self, job_id: str, doc_ids: List[str],
                        target_time: Optional[datetime] = None,
                        user_role: UserRole = UserRole.ADMIN) -> ScheduledUpdateJob:
        """Schedules a knowledge base update batch."""
        if not security_service.check_permission(user_role, "manage_kb"):
            raise PermissionError("Access Denied: You must be an ADMIN to schedule KB updates.")

        when = target_time or time_engine.now()
        job = ScheduledUpdateJob(
            job_id=job_id,
            scheduled_time=when,
            doc_ids=doc_ids,
            status="SCHEDULED"
        )
        self.jobs[job_id] = job
        audit_logger.log("INFO", f"KB Update Job '{job_id}' scheduled for {when.isoformat()}. Documents: {doc_ids}")
        return job

    def execute_job(self, job_id: str, simulated_failure: bool = False,
                    user_role: UserRole = UserRole.ADMIN) -> Dict[str, Any]:
        """
        Attempts execution of a scheduled update job:
        1. Checks RBAC.
        2. Enforces Maintenance Window gate.
        3. Runs Quality Gate tests.
        4. Activates documents on success, or schedules retries at 15m, 30m, 60m on failure.
        """
        if not security_service.check_permission(user_role, "publish_kb"):
            raise PermissionError("Access Denied: Only ADMIN can publish or activate KB updates.")

        if job_id not in self.jobs:
            raise KeyError(f"Job '{job_id}' not found.")

        job = self.jobs[job_id]
        now = time_engine.now()
        job.last_attempt_time = now
        # 1. Maintenance Window Enforcement
        in_maint_window = time_engine.is_within_maintenance_window(now)
        if not in_maint_window:
            reason = "Outside Maintenance Window (Allowed: 01:00 - 05:00). Activation deferred."
            job.status = "DEFERRED_OUTSIDE_MAINTENANCE_WINDOW"
            job.failure_reason = reason
            audit_logger.log("WARNING", f"Job '{job_id}' deferred: {reason}")
            return {
                "job_id": job_id,
                "status": job.status,
                "activated": False,
                "reason": reason
            }

        job.attempt_count += 1

        # 2. Simulated transient system failure / outage
        if simulated_failure:
            return self._handle_retry(job, "Transient service outage / upstream indexing failure.")

        # 3. Retrieve staged docs for this job
        staged_docs = [kb_pipeline.staged_store[did] for did in job.doc_ids if did in kb_pipeline.staged_store]

        # 4. Run Quality Gate
        eval_res = quality_gate.evaluate_staged_documents(staged_docs)
        if not eval_res.passed:
            job.status = "REJECTED_QUALITY_FAILURE"
            job.failure_reason = eval_res.message
            return {
                "job_id": job_id,
                "status": job.status,
                "activated": False,
                "reason": eval_res.message,
                "metrics": eval_res.to_dict()
            }

        # 5. Successfully Activate
        for doc in staged_docs:
            doc.status = "ACTIVE"
            kb_pipeline.active_store[doc.doc_id] = doc
            if doc.doc_id in kb_pipeline.staged_store:
                del kb_pipeline.staged_store[doc.doc_id]

        job.status = "ACTIVE"
        job.failure_reason = None
        audit_logger.log("INFO", f"Job '{job_id}' successfully activated during maintenance window! {len(staged_docs)} documents live.")

        return {
            "job_id": job_id,
            "status": "ACTIVE",
            "activated": True,
            "activated_count": len(staged_docs),
            "activation_time": now.isoformat()
        }

    def _handle_retry(self, job: ScheduledUpdateJob, error_msg: str) -> Dict[str, Any]:
        """Calculates next retry interval: 15, 30, 60 minutes."""
        now = time_engine.now()
        attempt_idx = job.attempt_count - 1 # 0, 1, 2

        if attempt_idx < len(job.retry_delays_minutes):
            delay_minutes = job.retry_delays_minutes[attempt_idx]
            next_retry_time = now + timedelta(minutes=delay_minutes)
            job.scheduled_time = next_retry_time
            job.status = f"RETRYING_IN_{delay_minutes}M"
            job.failure_reason = error_msg
            audit_logger.log("WARNING", f"Job '{job.job_id}' failed (Attempt {job.attempt_count}). Scheduled retry in {delay_minutes} min at {next_retry_time.isoformat()}. Error: {error_msg}")
            return {
                "job_id": job.job_id,
                "status": job.status,
                "activated": False,
                "attempt": job.attempt_count,
                "next_retry_time": next_retry_time.isoformat(),
                "delay_minutes": delay_minutes,
                "error": error_msg
            }
        else:
            job.status = "FAILED_PERMANENTLY"
            job.failure_reason = f"All {job.max_retries} retries exhausted. {error_msg}"
            audit_logger.log("ERROR", f"Job '{job.job_id}' permanently failed after exhausting retry schedule.")
            return {
                "job_id": job.job_id,
                "status": "FAILED_PERMANENTLY",
                "activated": False,
                "attempt": job.attempt_count,
                "error": job.failure_reason
            }

kb_scheduler = KBScheduler()
