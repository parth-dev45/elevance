"""
Task 4: Temporal & RBAC Guarded Policy Retriever.
Enforces access control (RBAC), filters future/expired policies for current queries,
retrieves active policies for historical dates, and resolves conflicting policies by picking latest applicable version.
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date
import re
from core.security import UserRole, security_service
from core.time_engine import time_engine
from core.logger import audit_logger
from task4_rag_assistant.vector_store import RAGDocument, rag_vector_store

class TemporalRetriever:
    DATE_REGEXES = [
        re.compile(r'\b(\d{4}-\d{2}-\d{2})\b'), # YYYY-MM-DD
        re.compile(r'\b(?:on|in|dated|as of)\s+([A-Z][a-z]+(?:\s+\d{1,2})?,?\s+\d{4})\b', re.IGNORECASE),
        re.compile(r'\b(?:back in|year)\s+(\d{4})\b', re.IGNORECASE)
    ]

    MONTH_MAP = {
        "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
        "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
        "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12
    }

    def extract_historical_date(self, query: str) -> Optional[date]:
        """Extracts customer-specified historical date if present in query."""
        # 1. ISO format YYYY-MM-DD
        match_iso = self.DATE_REGEXES[0].search(query)
        if match_iso:
            try:
                return datetime.strptime(match_iso.group(1), "%Y-%m-%d").date()
            except ValueError:
                pass

        # 2. Text month format e.g. "May 15, 2023" or "May 2023"
        match_text = self.DATE_REGEXES[1].search(query)
        if match_text:
            raw_str = match_text.group(1)
            parts = re.split(r'[\s,]+', raw_str.strip())
            if len(parts) >= 2:
                month_name = parts[0].lower()
                month_num = self.MONTH_MAP.get(month_name)
                if month_num:
                    try:
                        year = int(parts[-1])
                        day = int(parts[1]) if len(parts) >= 3 and parts[1].isdigit() else 1
                        return date(year, month_num, day)
                    except ValueError:
                        pass

        # 3. Simple Year
        match_year = self.DATE_REGEXES[2].search(query)
        if match_year:
            try:
                year = int(match_year.group(1))
                return date(year, 1, 1)
            except ValueError:
                pass

        return None

    def is_authorized(self, doc: RAGDocument, role: UserRole) -> bool:
        """Enforces Role-Based Access Control on document access level."""
        level = (doc.access_level or "public").lower()
        if level == "public":
            return True
        elif level == "internal":
            return role in [UserRole.AGENT, UserRole.SUPERVISOR, UserRole.ADMIN]
        elif level == "confidential":
            return role in [UserRole.SUPERVISOR, UserRole.ADMIN]
        return False

    def is_temporally_valid(self, doc: RAGDocument, target_date: date) -> bool:
        """
        Checks whether document was actively in effect on target_date.
        Excludes future policies (effective_date > target_date)
        and expired policies (expiry_date < target_date).
        """
        try:
            eff_date = datetime.strptime(doc.effective_date, "%Y-%m-%d").date()
        except ValueError:
            eff_date = date(2020, 1, 1)

        if eff_date > target_date:
            return False # Future policy

        if doc.expiry_date:
            try:
                exp_date = datetime.strptime(doc.expiry_date, "%Y-%m-%d").date()
                if exp_date < target_date:
                    return False # Expired policy
            except ValueError:
                pass

        return True

    def retrieve(self, query: str, user_role: UserRole = UserRole.CUSTOMER,
                  top_k: int = 3, explicit_date: Optional[date] = None) -> List[tuple[RAGDocument, float]]:
        """
        Retrieves relevant documents enforcing:
        1. Access level authorization (RBAC)
        2. Temporal validity for current or historical date
        3. Conflict resolution (picking latest applicable version)
        """
        # Determine target date
        hist_date = explicit_date or self.extract_historical_date(query)
        target_date = hist_date if hist_date else time_engine.now().date()
        is_historical = (hist_date is not None)

        # 1. Semantic search candidates from vector store
        candidates = rag_vector_store.search_similar(query, top_k=15)

        # 2. Filter by RBAC & Temporal validity
        valid_candidates = []
        for doc, score in candidates:
            if not self.is_authorized(doc, user_role):
                audit_logger.log("DEBUG", f"RBAC filtered out restricted doc '{doc.doc_id}' for role '{user_role.value}'.")
                continue
            if not self.is_temporally_valid(doc, target_date):
                audit_logger.log("DEBUG", f"Temporal filter excluded doc '{doc.doc_id}' (effective: {doc.effective_date}, expiry: {doc.expiry_date}) for target date {target_date.isoformat()}.")
                continue
            valid_candidates.append((doc, score))

        # 3. Resolve Conflicting Policies:
        # If multiple documents describe the same product/topic, pick the LATEST applicable version
        grouped_by_key: Dict[str, List[tuple[RAGDocument, float]]] = {}
        for doc, score in valid_candidates:
            key = f"{doc.product.lower()}::{re.split(r'[\s\-]+', doc.title.lower())[0]}"
            if key not in grouped_by_key:
                grouped_by_key[key] = []
            grouped_by_key[key].append((doc, score))

        resolved_docs: List[tuple[RAGDocument, float]] = []
        for key, group in grouped_by_key.items():
            if len(group) == 1:
                resolved_docs.append(group[0])
            else:
                # Conflict resolution: sort by effective_date desc, version desc
                def sort_key(item):
                    d, s = item
                    return (d.effective_date, d.version)
                best_doc = sorted(group, key=sort_key, reverse=True)[0]
                resolved_docs.append(best_doc)
                audit_logger.log("INFO", f"Resolved conflicting policy for '{key}'. Selected latest applicable version {best_doc[0].version} (effective {best_doc[0].effective_date}).")

        # Sort by relevance score desc and return top_k
        resolved_docs.sort(key=lambda x: x[1], reverse=True)
        return resolved_docs[:top_k]

temporal_retriever = TemporalRetriever()
