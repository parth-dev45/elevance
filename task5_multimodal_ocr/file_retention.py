"""
Task 5: File Retention and Automatic Lifecycle Purge Service.
Enforces data compliance by permanently deleting uploaded files after the configured retention period.
"""
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
from core.time_engine import time_engine
from core.config import config
from core.logger import audit_logger

class TrackedFile:
    def __init__(self, file_id: str, file_path: str, uploaded_at: datetime, retention_seconds: float):
        self.file_id = file_id
        self.file_path = file_path
        self.uploaded_at = uploaded_at
        self.retention_seconds = retention_seconds
        self.is_deleted = False

class FileRetentionManager:
    def __init__(self, upload_dir: str = "data/uploads"):
        self.upload_dir = upload_dir
        os.makedirs(self.upload_dir, exist_ok=True)
        self.tracked_files: Dict[str, TrackedFile] = {}

    def register_uploaded_file(self, file_path: str, custom_retention_seconds: Optional[float] = None) -> str:
        """Registers an uploaded file for automated lifecycle retention tracking."""
        file_id = f"FILE-{uuid.uuid4().hex[:8].upper()}"
        retention = custom_retention_seconds or config.file_retention_seconds
        tracked = TrackedFile(
            file_id=file_id,
            file_path=file_path,
            uploaded_at=time_engine.now(),
            retention_seconds=retention
        )
        self.tracked_files[file_id] = tracked
        audit_logger.log("INFO", f"Registered file '{file_id}' ({os.path.basename(file_path)}) with {retention}s retention period.")
        return file_id

    def purge_expired_files(self) -> List[str]:
        """
        Scans all tracked files against current simulated time.
        Permanently purges files exceeding configured retention period.
        """
        now = time_engine.now()
        purged = []

        for file_id, tracked in list(self.tracked_files.items()):
            if tracked.is_deleted:
                continue

            elapsed_seconds = (now - tracked.uploaded_at).total_seconds()
            if elapsed_seconds >= tracked.retention_seconds:
                # Delete from filesystem
                if os.path.exists(tracked.file_path):
                    try:
                        os.remove(tracked.file_path)
                    except OSError as e:
                        audit_logger.log("ERROR", f"Failed to delete expired file {tracked.file_path}: {str(e)}")

                tracked.is_deleted = True
                purged.append(file_id)
                audit_logger.log("INFO", f"DATA RETENTION PURGE: File '{file_id}' ({tracked.file_path}) permanently deleted after {round(elapsed_seconds/3600, 1)}h.")

        return purged

    def is_accessible(self, file_id: str) -> bool:
        """Verifies if a file is still within its valid retention lifecycle."""
        # Run purge check first
        self.purge_expired_files()

        if file_id not in self.tracked_files:
            return False

        tracked = self.tracked_files[file_id]
        if tracked.is_deleted or not os.path.exists(tracked.file_path):
            return False

        return True

file_retention_manager = FileRetentionManager()
