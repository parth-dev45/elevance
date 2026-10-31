"""
Task 4: High-Level RAG Knowledge Assistant.
Combines temporal retrieval, RBAC enforcement, policy conflict resolution,
guardrail sanitization, grounded answering, and mandatory source citations.
"""
from typing import Dict, Any, List, Optional
from datetime import date
from core.security import UserRole, security_service
from core.logger import audit_logger
from task4_rag_assistant.temporal_retriever import temporal_retriever, RAGDocument
from task4_rag_assistant.guardrails import rag_guardrails

class RAGAssistant:
    def __init__(self):
        pass

    def answer_query(self, query: str, user_role: UserRole = UserRole.CUSTOMER,
                     explicit_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Executes end-to-end RAG query:
        1. Checks for malicious user prompt injection.
        2. Retrieves temporally valid, RBAC-authorized documents (resolving conflicts).
        3. Sanitizes retrieved document content against embedded injection attacks.
        4. Synthesizes grounded answer or generates refusal if evidence is missing/ambiguous.
        5. Appends mandatory source citations.
        """
        # Step 1: User prompt injection check
        has_injection, inject_reason = security_service.detect_prompt_injection(query)
        if has_injection:
            audit_logger.log("WARNING", f"User Prompt Injection Blocked: {inject_reason}")
            return {
                "answer": "I cannot fulfill this request as it contains unauthorized instructions or attempts to bypass system policies.",
                "sources": [],
                "is_refusal": True,
                "confidence": 0.0,
                "reason": "prompt_injection_blocked"
            }

        # Step 2: Temporal & RBAC Document Retrieval
        retrieved_docs_with_scores = temporal_retriever.retrieve(
            query=query,
            user_role=user_role,
            top_k=2,
            explicit_date=explicit_date
        )

        # Step 3: Evidence check
        if not retrieved_docs_with_scores:
            refusal_msg = rag_guardrails.generate_refusal_clarification(query, reason="insufficient_evidence")
            audit_logger.log("INFO", f"RAG Refusal: No authorized, temporally valid evidence found for query: '{query[:60]}'")
            return {
                "answer": refusal_msg,
                "sources": [],
                "is_refusal": True,
                "confidence": 0.40,
                "reason": "missing_or_expired_evidence"
            }

        primary_doc, score = retrieved_docs_with_scores[0]
        source_docs = [d for d, s in retrieved_docs_with_scores]

        # Step 4: Sanitize documents against embedded prompt injections
        sanitized_content = rag_guardrails.sanitize_document_text(primary_doc.content)

        # Step 5: Answer synthesis grounded strictly on source content
        # Synthesize clear answer using verified document facts
        synthesis_lines = []
        for line in sanitized_content.splitlines():
            clean = line.strip()
            if clean and not clean.startswith("#"):
                synthesis_lines.append(clean)
        
        core_answer = " ".join(synthesis_lines[:4]) if synthesis_lines else sanitized_content

        # Step 6: Verify grounding
        is_grounded, unsupported = rag_guardrails.verify_grounding(core_answer, source_docs)
        if not is_grounded:
            audit_logger.log("WARNING", f"Unsupported claims detected in RAG synthesis: {unsupported}")
            core_answer = sanitized_content

        # Step 7: Append mandatory citations
        citations = rag_guardrails.format_citations(source_docs)
        final_response = f"{core_answer}{citations}"

        return {
            "answer": final_response,
            "sources": [d.to_dict() for d in source_docs],
            "is_refusal": False,
            "confidence": min(0.95, round(score + 0.35, 2)),
            "applied_doc_id": primary_doc.doc_id,
            "applied_version": primary_doc.version,
            "applied_effective_date": primary_doc.effective_date
        }

rag_assistant = RAGAssistant()
