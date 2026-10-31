"""
Task 1: Escalation Engine.
Monitors conversation health, sentiment patterns, high-risk topics, and time thresholds.
Routes to on-call queue or next business day schedule when after-hours.
Records reason, activated condition, and conversation summary for every escalation.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from core.time_engine import time_engine
from core.logger import audit_logger
from core.security import security_service
from core.config import config
from task1_sentiment_escalation.sentiment_analyzer import SentimentResult, sentiment_analyzer

class EscalationDecision:
    def __init__(self, is_escalated: bool, reason: Optional[str] = None,
                 activated_condition: Optional[str] = None,
                 target_queue: Optional[str] = None,
                 conversation_summary: Optional[str] = None,
                 scheduled_time: Optional[datetime] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        self.is_escalated = is_escalated
        self.reason = reason
        self.activated_condition = activated_condition
        self.target_queue = target_queue
        self.conversation_summary = conversation_summary
        self.scheduled_time = scheduled_time
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_escalated": self.is_escalated,
            "reason": self.reason,
            "activated_condition": self.activated_condition,
            "target_queue": self.target_queue,
            "conversation_summary": self.conversation_summary,
            "scheduled_time": self.scheduled_time.isoformat() if self.scheduled_time else None,
            "metadata": self.metadata
        }

class EscalationEngine:
    def __init__(self):
        pass

    def generate_conversation_summary(self, history: List[Dict[str, Any]], current_message: str) -> str:
        """Constructs an anonymized summary of the customer's conversation."""
        lines = []
        for turn in history:
            role = turn.get("role", "user").capitalize()
            content = turn.get("content", "")
            lines.append(f"{role}: {content}")
        lines.append(f"Customer: {current_message}")
        full_text = "\n".join(lines)
        return security_service.mask_pii(full_text)

    def evaluate(self, current_message: str,
                 sentiment_res: SentimentResult,
                 history: List[Dict[str, Any]] = None,
                 conversation_start_time: Optional[datetime] = None,
                 first_negative_time: Optional[datetime] = None) -> EscalationDecision:
        """
        Evaluates current state against escalation criteria:
        1. High-risk issues (account compromise, duplicate payment, legal threats).
        2. Repeated negative messages.
        3. Negative conversation unresolved > 15 minutes.
        4. After-hours handling (urgent -> on-call; normal -> next business day).
        """
        history = history or []
        current_time = time_engine.now()
        is_in_business_hours = time_engine.is_within_business_hours(current_time)

        # 1. High-Risk Issue Check (Calm or Angry)
        if sentiment_res.high_risk_flags:
            risk_type = sentiment_res.high_risk_flags[0]
            reason = f"High-risk issue detected: {risk_type.replace('_', ' ').title()}"
            condition = f"high_risk_trigger: {risk_type}"
            summary = self.generate_conversation_summary(history, current_message)

            target_queue = "live_agent_queue" if is_in_business_hours else "on_call_emergency_queue"
            
            audit_logger.log_escalation(
                reason=reason,
                activated_condition=condition,
                conversation_summary=summary,
                details={"risk_flags": sentiment_res.high_risk_flags, "after_hours": not is_in_business_hours}
            )

            return EscalationDecision(
                is_escalated=True,
                reason=reason,
                activated_condition=condition,
                target_queue=target_queue,
                conversation_summary=summary,
                metadata={"high_risk_flags": sentiment_res.high_risk_flags}
            )

        # 2. Negative Conversation Unresolved > 15 minutes Check
        if first_negative_time is not None:
            elapsed_seconds = (current_time - first_negative_time).total_seconds()
            if elapsed_seconds >= (config.negative_escalation_minutes * 60):
                reason = f"Negative conversation unresolved for {round(elapsed_seconds/60, 1)} minutes (exceeded 15 min SLA)"
                condition = f"unresolved_negative_duration_exceeded (>={config.negative_escalation_minutes}m)"
                summary = self.generate_conversation_summary(history, current_message)

                if is_in_business_hours:
                    target_queue = "live_agent_queue"
                    scheduled_time = None
                else:
                    if sentiment_res.is_urgent:
                        target_queue = "on_call_emergency_queue"
                        scheduled_time = None
                    else:
                        target_queue = "scheduled_next_business_day"
                        scheduled_time = time_engine.get_next_business_day_start(current_time)

                audit_logger.log_escalation(
                    reason=reason,
                    activated_condition=condition,
                    conversation_summary=summary,
                    details={"elapsed_minutes": round(elapsed_seconds / 60, 2)}
                )

                return EscalationDecision(
                    is_escalated=True,
                    reason=reason,
                    activated_condition=condition,
                    target_queue=target_queue,
                    conversation_summary=summary,
                    scheduled_time=scheduled_time,
                    metadata={"unresolved_minutes": elapsed_seconds / 60}
                )

        # 3. Repeated Negative Messages Check
        negative_count = 0
        consecutive_negative = 0
        if sentiment_res.primary_sentiment in ["negative", "frustrated", "sarcastic"]:
            negative_count += 1
            consecutive_negative += 1

        for turn in reversed(history):
            if turn.get("role") in ["user", "customer"]:
                turn_sentiment = turn.get("sentiment")
                if turn_sentiment in ["negative", "frustrated", "sarcastic"]:
                    negative_count += 1
                    consecutive_negative += 1
                else:
                    break

        if consecutive_negative >= 2 or negative_count >= 3:
            reason = "Customer expressing repeated negative sentiment or persistent frustration"
            condition = f"repeated_negative_messages_threshold (consecutive={consecutive_negative}, total={negative_count})"
            summary = self.generate_conversation_summary(history, current_message)
            
            # Determine queue based on urgency & business hours
            if is_in_business_hours:
                target_queue = "live_agent_queue"
                scheduled_time = None
            else:
                if sentiment_res.is_urgent:
                    target_queue = "on_call_emergency_queue"
                    scheduled_time = None
                else:
                    target_queue = "scheduled_next_business_day"
                    scheduled_time = time_engine.get_next_business_day_start(current_time)

            audit_logger.log_escalation(
                reason=reason,
                activated_condition=condition,
                conversation_summary=summary,
                details={"negative_count": negative_count, "consecutive": consecutive_negative}
            )

            return EscalationDecision(
                is_escalated=True,
                reason=reason,
                activated_condition=condition,
                target_queue=target_queue,
                conversation_summary=summary,
                scheduled_time=scheduled_time,
                metadata={"negative_count": negative_count}
            )

        # 4. Check if complaint is urgent outside business hours (even if first time)
        if sentiment_res.is_urgent and not is_in_business_hours:
            reason = "Urgent customer complaint received outside business hours"
            condition = "after_hours_urgent_ticket"
            summary = self.generate_conversation_summary(history, current_message)

            audit_logger.log_escalation(
                reason=reason,
                activated_condition=condition,
                conversation_summary=summary,
                details={"after_hours": True, "urgent": True}
            )

            return EscalationDecision(
                is_escalated=True,
                reason=reason,
                activated_condition=condition,
                target_queue="on_call_emergency_queue",
                conversation_summary=summary,
                metadata={"on_call_alert": True}
            )

        # 5. Non-urgent complaint received outside business hours
        is_complaint = (
            sentiment_res.primary_sentiment in ["negative", "frustrated", "sarcastic"] or
            any(w in current_message.lower() for w in ["complaint", "issue", "problem", "not satisfied", "wrong", "broken", "delay"])
        )
        if is_complaint and not is_in_business_hours:
            reason = "Complaint received outside business hours (standard priority)"
            condition = "after_hours_standard_ticket"
            summary = self.generate_conversation_summary(history, current_message)
            scheduled_start = time_engine.get_next_business_day_start(current_time)

            audit_logger.log_escalation(
                reason=reason,
                activated_condition=condition,
                conversation_summary=summary,
                details={"after_hours": True, "scheduled_start": scheduled_start.isoformat()}
            )

            return EscalationDecision(
                is_escalated=True,
                reason=reason,
                activated_condition=condition,
                target_queue="scheduled_next_business_day",
                conversation_summary=summary,
                scheduled_time=scheduled_start,
                metadata={"scheduled_for_workday": True}
            )

        # Not escalated
        return EscalationDecision(is_escalated=False)

escalation_engine = EscalationEngine()
