"""
Task 5: Document & Image File Sanitizer.
Rejects unsafe file types, executable binaries, oversized payloads,
and malicious prompt-injection instructions hidden inside images or documents.
"""
import os
from typing import Tuple, Optional
from core.security import security_service
from core.logger import audit_logger
from core.config import config

class DocumentSanitizer:
    DANGEROUS_EXTENSIONS = {
        ".exe", ".sh", ".bat", ".cmd", ".py", ".js", ".vbs", ".bin",
        ".msi", ".dll", ".so", ".apk", ".jar", ".ps1", ".com"
    }
    ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".pdf"}
    MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024 # 15 MB

    def sanitize_file(self, file_path: str, raw_extracted_text: Optional[str] = None) -> Tuple[bool, str]:
        """
        Validates file safety:
        1. Checks file extension against dangerous/executable list.
        2. Enforces allowed mime types.
        3. Checks file size bounds.
        4. Scans raw text / OCR text for hidden prompt injection attacks.
        Returns: (is_safe: bool, reason: str)
        """
        if not os.path.exists(file_path):
            return False, "File does not exist."

        filename = os.path.basename(file_path)
        ext = os.path.splitext(filename)[1].lower()

        # 1. Reject dangerous executable files
        if ext in self.DANGEROUS_EXTENSIONS:
            reason = f"Security Violation: Prohibited executable file type '{ext}'."
            audit_logger.log("ERROR", f"File upload rejected: {filename}. {reason}")
            return False, reason

        # 2. Enforce allowed document/image types
        if ext not in self.ALLOWED_EXTENSIONS:
            reason = f"Unsupported file type '{ext}'. Allowed types: PNG, JPG, WEBP, PDF."
            audit_logger.log("WARNING", f"File upload rejected: {filename}. {reason}")
            return False, reason

        # 3. File size check
        file_size = os.path.getsize(file_path)
        if file_size > self.MAX_FILE_SIZE_BYTES:
            reason = f"File size ({round(file_size/(1024*1024), 2)}MB) exceeds maximum limit of 15MB."
            audit_logger.log("WARNING", f"File upload rejected: {filename}. {reason}")
            return False, reason

        # 4. Prompt injection check inside file content / OCR text
        if raw_extracted_text:
            has_injection, inject_reason = security_service.detect_prompt_injection(raw_extracted_text)
            if has_injection:
                reason = f"Security Violation: Malicious prompt injection payload hidden inside document ({inject_reason})."
                audit_logger.log("ERROR", f"File rejected: {filename}. {reason}")
                return False, reason

        return True, "File is safe and verified."

document_sanitizer = DocumentSanitizer()
