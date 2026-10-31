"""
Task 3: Production Knowledge Base Ingestion Pipeline.
Processes only new or modified documents, detects duplicates, quarantines invalid files,
enforces content hashing, prompt-injection defense, and RBAC permissions.
"""
import hashlib
import os
import shutil
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field
from datetime import datetime
from core.security import security_service, UserRole
from core.time_engine import time_engine
from core.logger import audit_logger

class KBDocument(BaseModel):
    doc_id: str
    title: str
    content: str
    version: str = "1.0"
    product: str = "general"
    region: str = "GLOBAL"
    access_level: str = "public" # public, internal, confidential
    effective_date: str = "2020-01-01"
    expiry_date: Optional[str] = None
    content_hash: str = ""
    status: str = "STAGED" # STAGED, ACTIVE, QUARANTINED, REJECTED, ARCHIVED
    quarantine_reason: Optional[str] = None
    created_at: str = Field(default_factory=lambda: time_engine.now().isoformat())

class IngestionResult(BaseModel):
    total_processed: int = 0
    new_docs: List[str] = Field(default_factory=list)
    modified_docs: List[str] = Field(default_factory=list)
    duplicate_docs: List[str] = Field(default_factory=list)
    quarantined_docs: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)

class KBPipeline:
    def __init__(self, quarantine_dir: str = "data/quarantine"):
        self.quarantine_dir = quarantine_dir
        os.makedirs(self.quarantine_dir, exist_ok=True)
        # Store for processed documents by doc_id
        self.active_store: Dict[str, KBDocument] = {}
        self.staged_store: Dict[str, KBDocument] = {}
        self.history_store: Dict[str, List[KBDocument]] = {}
        self.known_hashes: Dict[str, str] = {} # hash -> doc_id

    def compute_hash(self, content: str, title: str, metadata: Dict[str, Any]) -> str:
        """Computes SHA-256 hash across content, title, and key metadata attributes."""
        raw = f"{title.strip()}::{content.strip()}::{metadata.get('product')}::{metadata.get('region')}::{metadata.get('access_level')}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def quarantine_file(self, doc_id: str, filename: str, content: str, reason: str):
        """Moves corrupted or unsafe files to the quarantine vault."""
        filepath = os.path.join(self.quarantine_dir, f"{doc_id}_{filename}.txt")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"REASON: {reason}\nDATE: {time_engine.now().isoformat()}\n---\n{content}")
        audit_logger.log("WARNING", f"QUARANTINED: Document '{doc_id}' quarantined. Reason: {reason}")

    def ingest_documents(self, raw_documents: List[Dict[str, Any]], user_role: UserRole = UserRole.ADMIN) -> IngestionResult:
        """
        Ingests batch of documents with RBAC check, delta processing (only new or modified),
        duplicate detection, prompt-injection sanitization, and quarantine isolation.
        """
        # RBAC Check: Only ADMIN can manage the knowledge base
        if not security_service.check_permission(user_role, "manage_kb"):
            audit_logger.log("ERROR", f"UNAUTHORIZED ACCESS ATTEMPT: Role '{user_role.value}' attempted KB ingestion.")
            raise PermissionError(f"Access Denied: Role '{user_role.value}' is not authorized to ingest knowledge base documents.")

        result = IngestionResult(total_processed=len(raw_documents))

        for item in raw_documents:
            doc_id = item.get("doc_id")
            title = item.get("title", "")
            content = item.get("content", "")
            metadata = item.get("metadata", {})

            # 1. Validation check: required fields
            if not doc_id or not content or not title:
                reason = "Invalid format: missing doc_id, title, or content"
                result.quarantined_docs.append(doc_id or "UNKNOWN")
                self.quarantine_file(doc_id or "INVALID", "malformed", str(item), reason)
                continue

            # 2. Prompt injection defense check within documents
            has_injection, inject_reason = security_service.detect_prompt_injection(content)
            if has_injection:
                reason = f"Security Violation: {inject_reason}"
                result.quarantined_docs.append(doc_id)
                self.quarantine_file(doc_id, "injection_payload", content, reason)
                continue

            # 3. PII masking on ingested content
            safe_content = security_service.mask_pii(content)
            content_hash = self.compute_hash(safe_content, title, metadata)

            # 4. Duplicate Detection
            # If identical hash already exists in active or staged store
            if content_hash in self.known_hashes:
                existing_doc_id = self.known_hashes[content_hash]
                result.duplicate_docs.append(doc_id)
                audit_logger.log("INFO", f"Skipping duplicate document '{doc_id}' (identical content to '{existing_doc_id}').")
                continue

            # 5. Check if it's an update to existing doc_id or a brand new document
            is_modified = (doc_id in self.active_store or doc_id in self.staged_store)
            
            kb_doc = KBDocument(
                doc_id=doc_id,
                title=title,
                content=safe_content,
                version=item.get("version", "1.0"),
                product=metadata.get("product", "general"),
                region=metadata.get("region", "GLOBAL"),
                access_level=metadata.get("access_level", "public"),
                effective_date=metadata.get("effective_date", "2020-01-01"),
                expiry_date=metadata.get("expiry_date"),
                content_hash=content_hash,
                status="STAGED"
            )

            # Stage for quality gate evaluation
            self.staged_store[doc_id] = kb_doc
            self.known_hashes[content_hash] = doc_id

            if is_modified:
                result.modified_docs.append(doc_id)
                audit_logger.log("INFO", f"Staged modified document '{doc_id}' version {kb_doc.version}.")
            else:
                result.new_docs.append(doc_id)
                audit_logger.log("INFO", f"Staged new document '{doc_id}' version {kb_doc.version}.")

        return result

kb_pipeline = KBPipeline()
