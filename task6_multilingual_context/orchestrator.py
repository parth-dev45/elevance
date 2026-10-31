"""
Master Chatbot Orchestrator: Unifies Tasks 1 through 6.
Handles multilingual processing, session lifecycle, sentiment escalation,
structured ticket handoff, and temporal RAG answering.
"""
from typing import Dict, Any, List, Optional
import time
from core.time_engine import time_engine
from core.security import UserRole, security_service
from core.logger import audit_logger
from task1_sentiment_escalation.sentiment_analyzer import sentiment_analyzer
from task1_sentiment_escalation.tone_adapter import tone_adapter
from task1_sentiment_escalation.escalation_engine import escalation_engine
from task2_ticket_sla.entity_extractor import entity_extractor
from task2_ticket_sla.priority_calculator import priority_calculator
from task2_ticket_sla.routing_engine import routing_engine
from task2_ticket_sla.sla_manager import sla_manager
from task2_ticket_sla.ticket_clusterer import ticket_clusterer
from task4_rag_assistant.assistant import rag_assistant
from task6_multilingual_context.language_manager import language_manager
from task6_multilingual_context.transliteration_normalizer import transliteration_normalizer
from task6_multilingual_context.entity_preserver import entity_preserver
from task6_multilingual_context.session_manager import session_manager, CustomerSession

class BotResponse:
    def __init__(self, response_text: str, session_id: str, detected_language: str,
                 sentiment: str, is_escalated: bool = False,
                 escalation_queue: Optional[str] = None,
                 ticket_created: Optional[Dict[str, Any]] = None,
                 sources: Optional[List[Dict[str, Any]]] = None,
                 session_action: Optional[str] = None,
                 requires_clarification: bool = False):
        self.response_text = response_text
        self.session_id = session_id
        self.detected_language = detected_language
        self.sentiment = sentiment
        self.is_escalated = is_escalated
        self.escalation_queue = escalation_queue
        self.ticket_created = ticket_created
        self.sources = sources or []
        self.session_action = session_action
        self.requires_clarification = requires_clarification

    def to_dict(self) -> Dict[str, Any]:
        return {
            "response_text": self.response_text,
            "session_id": self.session_id,
            "detected_language": self.detected_language,
            "sentiment": self.sentiment,
            "is_escalated": self.is_escalated,
            "escalation_queue": self.escalation_queue,
            "ticket": self.ticket_created,
            "sources": self.sources,
            "session_action": self.session_action,
            "requires_clarification": self.requires_clarification
        }

class ChatbotOrchestrator:
    def __init__(self):
        pass

    def process_turn(self, customer_id: str, message: str,
                     user_role: UserRole = UserRole.CUSTOMER,
                     customer_tier: str = "standard") -> BotResponse:
        """
        Orchestrates full conversation turn across all assignment tasks.
        """
        start_time = time.time()

        # 1. Multi-Tenant Session Isolation & Lifecycle
        session, session_action = session_manager.get_or_create_session(customer_id)
        session_id = session.session_id

        # 2. Entity Protection: preserve names, order IDs, dates, SKUs
        protected_msg, token_map = entity_preserver.protect_entities(message)

        # 3. Transliteration Normalization & Spelling Correction
        normalized_msg = transliteration_normalizer.normalize_transliteration(protected_msg)
        corrected_msg = transliteration_normalizer.correct_spelling(normalized_msg)
        unprotected_clean_msg = entity_preserver.restore_entities(corrected_msg, token_map)

        # 4. Multilingual & Code-Switching Detection
        lang_res = language_manager.detect_language(unprotected_clean_msg, previous_language=session.language)
        session.language = lang_res.language

        # If language confidence is below threshold, request clarification
        if lang_res.requires_clarification and len(session.history) == 0:
            session_manager.add_message(session_id, role="user", content=message, language=lang_res.language)
            session_manager.add_message(session_id, role="assistant", content=lang_res.clarification_prompt, language=lang_res.language)
            return BotResponse(
                response_text=lang_res.clarification_prompt,
                session_id=session_id,
                detected_language=lang_res.language,
                sentiment="neutral",
                session_action=session_action,
                requires_clarification=True
            )

        # 5. Extract Entities & Check for User Corrections
        correction_info = transliteration_normalizer.extract_corrected_information(unprotected_clean_msg)
        extracted_entities = entity_extractor.extract(
            unprotected_clean_msg,
            history=[t.model_dump() for t in session.history],
            known_customer=session.extracted_entities.get("customer")
        )
        if correction_info.get("has_correction") and correction_info.get("field") == "order_id":
            extracted_entities.order_id = correction_info["corrected_val"]
            audit_logger.log("INFO", f"Applied user correction for order_id: {correction_info['corrected_val']}")

        # Merge extracted entities into session state
        for k, v in extracted_entities.model_dump().items():
            if v and k not in ["missing_fields", "is_complete", "clarification_prompt"]:
                session.extracted_entities[k] = v

        # 6. Sentiment, Sarcasm & High-Risk Analysis
        history_dicts = [{"role": t.role, "content": t.content, "sentiment": t.sentiment} for t in session.history]
        sentiment_res = sentiment_analyzer.analyze_message(unprotected_clean_msg, history=history_dicts)

        # Find first negative message timestamp in history
        first_neg_time = None
        for t in session.history:
            if t.sentiment in ["negative", "frustrated", "sarcastic"]:
                first_neg_time = t.timestamp
                break
        if not first_neg_time and sentiment_res.primary_sentiment in ["negative", "frustrated", "sarcastic"]:
            first_neg_time = time_engine.now()

        # 7. Escalation Engine Evaluation
        escalation_decision = escalation_engine.evaluate(
            current_message=unprotected_clean_msg,
            sentiment_res=sentiment_res,
            history=history_dicts,
            conversation_start_time=session.created_at,
            first_negative_time=first_neg_time
        )

        ticket_payload = None

        # 8. Handling Escalation & Structured Ticket Generation
        if escalation_decision.is_escalated:
            # Calculate multi-factor priority
            priority_info = priority_calculator.calculate_priority(
                issue_text=extracted_entities.issue or unprotected_clean_msg,
                sentiment=sentiment_res.primary_sentiment,
                is_urgent=sentiment_res.is_urgent,
                waiting_time_hours=0.0,
                customer_tier=customer_tier,
                high_risk_flags=sentiment_res.high_risk_flags,
                is_escalated=True
            )

            # Route Ticket using Agent Skills & Availability
            routing_res = routing_engine.route_ticket(
                issue_text=extracted_entities.issue or unprotected_clean_msg,
                priority_tier=priority_info["tier"],
                is_urgent=sentiment_res.is_urgent
            )

            # Check if duplicate request exists
            is_dup, orig_id = ticket_clusterer.detect_duplicate(
                candidate_issue=extracted_entities.issue or unprotected_clean_msg,
                customer=extracted_entities.customer or customer_id,
                order_id=extracted_entities.order_id,
                active_tickets=list(sla_manager.tickets.values())
            )

            if is_dup:
                ticket_msg = f"We have noted your follow-up regarding existing Ticket {orig_id}. An agent is actively reviewing your updates."
                ticket_payload = {"ticket_id": orig_id, "is_duplicate": True}
            else:
                # Create structured ticket
                new_ticket = sla_manager.create_ticket(
                    customer=extracted_entities.customer or customer_id,
                    issue=extracted_entities.issue or unprotected_clean_msg,
                    priority_tier=priority_info["tier"],
                    order_id=extracted_entities.order_id,
                    product=extracted_entities.product,
                    contact_details=extracted_entities.contact_details,
                    evidence=extracted_entities.evidence,
                    assigned_agent_id=routing_res.assigned_agent_id,
                    target_queue=routing_res.target_queue
                )
                # Generate masked handoff summary
                ticket_clusterer.generate_masked_handoff_summary(new_ticket, context=escalation_decision.conversation_summary)
                ticket_payload = new_ticket.model_dump()
                ticket_msg = f"Your request has been escalated to our {routing_res.target_queue.replace('_', ' ').title()}. Ticket ID: {new_ticket.ticket_id}."

            # Construct empathetic escalated response
            base_reply = f"{ticket_msg} Reason for escalation: {escalation_decision.reason}."
            if escalation_decision.target_queue == "on_call_emergency_queue":
                base_reply += " Our 24/7 on-call emergency support team has been dispatched."
            elif escalation_decision.target_queue == "scheduled_next_business_day":
                sched_str = escalation_decision.scheduled_time.strftime("%Y-%m-%d %H:%M") if escalation_decision.scheduled_time else "the next working day at 09:00 AM"
                base_reply += f" Our offices are currently closed. Your ticket is prioritized for {sched_str}."

            adapted_reply = tone_adapter.adapt_response(base_reply, sentiment=sentiment_res.primary_sentiment, is_urgent=sentiment_res.is_urgent)

            # Record session history
            session_manager.add_message(session_id, role="user", content=message, sentiment=sentiment_res.primary_sentiment, language=lang_res.language)
            session_manager.add_message(session_id, role="assistant", content=adapted_reply, sentiment="neutral", language=lang_res.language)

            elapsed_ms = (time.time() - start_time) * 1000
            audit_logger.record_metric(latency_ms=elapsed_ms, confidence=sentiment_res.confidence)

            return BotResponse(
                response_text=adapted_reply,
                session_id=session_id,
                detected_language=lang_res.language,
                sentiment=sentiment_res.primary_sentiment,
                is_escalated=True,
                escalation_queue=escalation_decision.target_queue,
                ticket_created=ticket_payload,
                session_action=session_action
            )

        # 9. If missing mandatory fields on an actionable query, request clarification
        if not extracted_entities.is_complete and extracted_entities.clarification_prompt and any(w in unprotected_clean_msg.lower() for w in ["refund", "cancel", "return", "broken", "delayed"]):
            clarification_reply = tone_adapter.adapt_response(
                extracted_entities.clarification_prompt,
                sentiment=sentiment_res.primary_sentiment
            )
            session_manager.add_message(session_id, role="user", content=message, sentiment=sentiment_res.primary_sentiment, language=lang_res.language)
            session_manager.add_message(session_id, role="assistant", content=clarification_reply, language=lang_res.language)
            return BotResponse(
                response_text=clarification_reply,
                session_id=session_id,
                detected_language=lang_res.language,
                sentiment=sentiment_res.primary_sentiment,
                session_action=session_action,
                requires_clarification=True
            )

        # 10. Temporal RAG Knowledge Assistant Query
        rag_res = rag_assistant.answer_query(
            query=unprotected_clean_msg,
            user_role=user_role
        )

        # 11. Modulate Tone without changing policy facts
        final_reply = tone_adapter.adapt_response(
            base_policy_message=rag_res["answer"],
            sentiment=sentiment_res.primary_sentiment,
            is_urgent=sentiment_res.is_urgent
        )

        # Record session history
        session_manager.add_message(session_id, role="user", content=message, sentiment=sentiment_res.primary_sentiment, language=lang_res.language)
        session_manager.add_message(session_id, role="assistant", content=final_reply, language=lang_res.language)

        elapsed_ms = (time.time() - start_time) * 1000
        audit_logger.record_metric(latency_ms=elapsed_ms, confidence=rag_res.get("confidence", 0.90))

        return BotResponse(
            response_text=final_reply,
            session_id=session_id,
            detected_language=lang_res.language,
            sentiment=sentiment_res.primary_sentiment,
            is_escalated=False,
            sources=rag_res.get("sources", []),
            session_action=session_action
        )

chatbot_orchestrator = ChatbotOrchestrator()
