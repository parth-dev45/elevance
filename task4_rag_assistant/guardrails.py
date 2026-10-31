"""
Task 4: Guardrails, Grounding Verification, Source Citations & Prompt-Injection Neutralizer.
Sanitizes malicious document payloads, detects unsupported claims, and requires exact source citations.
"""
from typing import List, Dict, Any, Tuple
import re
from core.security import security_service
from core.logger import audit_logger
from task4_rag_assistant.vector_store import RAGDocument

class RAGGuardrails:
    # Malicious injection cues to strip from retrieved document text
    MALICIOUS_INJECTION_SNIPPETS = [
        re.compile(r"ignore\s+(all\s+)?(previous|above|system)\s+(instructions|directives|prompts)", re.IGNORECASE),
        re.compile(r"system\s*override[:\s]+[^\n\.]+", re.IGNORECASE),
        re.compile(r"developer\s+mode[:\s]+[^\n\.]+", re.IGNORECASE),
        re.compile(r"grant\s+(free|unlimited|unauthorized)\s+refunds?", re.IGNORECASE),
        re.compile(r"bypass\s+(all\s+)?(policies|rules|security)", re.IGNORECASE),
    ]

    def sanitize_document_text(self, text: str) -> str:
        """
        Neutralizes prompt injection payloads embedded within retrieved documents
        so the assistant's reasoning is never hijacked by malicious documents.
        """
        sanitized = text
        for pattern in self.MALICIOUS_INJECTION_SNIPPETS:
            if pattern.search(sanitized):
                sanitized = pattern.sub("[REDACTED_MALICIOUS_INSTRUCTION]", sanitized)
                audit_logger.log("WARNING", "NEUTRALIZED malicious instruction embedded inside retrieved document.")
        return sanitized

    def verify_grounding(self, generated_answer: str, source_docs: List[RAGDocument]) -> Tuple[bool, List[str]]:
        """
        Verifies that factual claims (numbers, monetary amounts, time windows)
        in the generated response are grounded in the source documents.
        Returns: (is_grounded: bool, unsupported_facts: List[str])
        """
        if not source_docs:
            return False, ["No source documents provided"]

        combined_sources = " ".join([d.content for d in source_docs]).lower()
        unsupported = []

        # Extract monetary amounts e.g. $10, $5.99
        amounts = re.findall(r'\$\d+(?:\.\d{2})?', generated_answer)
        for amt in amounts:
            if amt.lower() not in combined_sources:
                unsupported.append(amt)

        # Extract time frames e.g. "14 days", "30 days"
        time_windows = re.findall(r'\b\d+\s+(?:days?|weeks?|months?|hours?)\b', generated_answer, re.IGNORECASE)
        for tw in time_windows:
            if tw.lower() not in combined_sources:
                unsupported.append(tw)

        is_grounded = (len(unsupported) == 0)
        return is_grounded, unsupported

    def format_citations(self, source_docs: List[RAGDocument]) -> str:
        """Formats strict source citations for every factual statement."""
        if not source_docs:
            return ""

        citations = []
        for d in source_docs:
            citations.append(f"- [Source: {d.title} (Doc ID: {d.doc_id}, Version: {d.version}, Effective: {d.effective_date})]")

        return "\n\n**Verified Policy Sources:**\n" + "\n".join(citations)

    def generate_refusal_clarification(self, query: str, reason: str = "insufficient_evidence") -> str:
        """
        Generates standard refusal or clarification prompt when evidence is missing or ambiguous.
        Never invents missing values.
        """
        if reason == "ambiguous":
            return (
                "Your request appears ambiguous or could refer to multiple policies. "
                "Could you please clarify your product model, region, or the specific date of purchase so I can look up the exact terms?"
            )
        return (
            "I could not locate verified company policy documentation to answer that specific inquiry. "
            "To prevent providing incorrect or unsupported information, could you please provide your order ID or specify the product name?"
        )

rag_guardrails = RAGGuardrails()
