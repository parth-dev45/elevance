"""
Task 3: Version Manager & Automated 5-Minute Canary Rollback.
Maintains version snapshots and executes automatic rollback if health checks fail within 5 minutes.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import copy
from core.time_engine import time_engine
from core.logger import audit_logger
from core.config import config
from core.security import security_service, UserRole
from task3_knowledge_pipeline.pipeline import kb_pipeline, KBDocument

class VersionSnapshot:
    def __init__(self, version_id: str, timestamp: datetime, documents: Dict[str, KBDocument]):
        self.version_id = version_id
        self.timestamp = timestamp
        self.documents = copy.deepcopy(documents)

class KBVersionManager:
    def __init__(self):
        self.snapshots: Dict[str, VersionSnapshot] = {}
        self.current_version_id: str = "v1.0"
        self.last_activation_time: Optional[datetime] = None
        self.previous_stable_version: Optional[str] = None

    def create_snapshot(self, version_id: str) -> VersionSnapshot:
        """Saves a point-in-time snapshot of the current active knowledge base."""
        now = time_engine.now()
        snap = VersionSnapshot(version_id, now, kb_pipeline.active_store)
        self.snapshots[version_id] = snap
        self.previous_stable_version = self.current_version_id
        self.current_version_id = version_id
        self.last_activation_time = now
        audit_logger.log("INFO", f"Created KB snapshot '{version_id}' with {len(snap.documents)} documents.")
        return snap

    def rollback_to(self, target_version_id: str, reason: str = "Manual Rollback",
                    user_role: UserRole = UserRole.ADMIN) -> Dict[str, Any]:
        """Restores knowledge base to target snapshot with RBAC enforcement."""
        if not security_service.check_permission(user_role, "rollback_kb"):
            raise PermissionError("Access Denied: Only ADMIN can perform KB rollbacks.")

        if target_version_id not in self.snapshots:
            raise KeyError(f"Snapshot version '{target_version_id}' does not exist.")

        target_snap = self.snapshots[target_version_id]
        kb_pipeline.active_store = copy.deepcopy(target_snap.documents)
        old_version = self.current_version_id
        self.current_version_id = target_version_id

        audit_logger.log("WARNING", f"KB ROLLBACK EXECUTED: Reverted from {old_version} to {target_version_id}. Reason: {reason}")
        return {
            "status": "ROLLED_BACK",
            "restored_version": target_version_id,
            "document_count": len(kb_pipeline.active_store),
            "reason": reason
        }

    def verify_canary_health(self, simulated_error_rate: float = 0.0,
                             force_health_failure: bool = False) -> Dict[str, Any]:
        """
        Monitors health within 5-minute canary window after activation.
        If errors or failure occurs within 5 minutes, executes automatic rollback!
        """
        now = time_engine.now()
        if not self.last_activation_time:
            return {"status": "HEALTHY", "canary_active": False}

        elapsed_seconds = (now - self.last_activation_time).total_seconds()
        is_in_canary_window = (0 <= elapsed_seconds <= (config.canary_health_check_minutes * 60))

        if is_in_canary_window:
            # Health check condition: error rate > 10% or explicit failure flag
            if force_health_failure or simulated_error_rate > 0.10:
                rollback_target = self.previous_stable_version or "v1.0"
                reason = f"Canary health check failed at {round(elapsed_seconds, 1)}s (<5m): error rate {round(simulated_error_rate*100, 1)}%"
                
                # Auto rollback
                rb_result = self.rollback_to(rollback_target, reason=f"AUTOMATIC_CANARY_ROLLBACK: {reason}")
                return {
                    "canary_passed": False,
                    "auto_rolled_back": True,
                    "target_version": rollback_target,
                    "elapsed_seconds": elapsed_seconds,
                    "reason": reason
                }

        return {
            "canary_passed": True,
            "auto_rolled_back": False,
            "current_version": self.current_version_id,
            "elapsed_seconds": elapsed_seconds,
            "window_expired": not is_in_canary_window
        }

kb_version_manager = KBVersionManager()
