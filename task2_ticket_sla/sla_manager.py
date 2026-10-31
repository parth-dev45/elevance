"""
Task 2: SLA Manager with Weekend & Holiday Exclusion, 75% Warning, and Breach Escalation.
Supports runtime updates to SLA policies and dynamic deadline recalculation.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import uuid
from core.time_engine import time_engine
from core.config import config
from core.logger import audit_logger

class Ticket(BaseModel):
    ticket_id: str
    customer: str
    order_id: Optional[str] = None
    product: Optional[str] = None
    issue: str
    contact_details: Optional[str] = None
    evidence: Optional[str] = None
    priority_tier: str = "MEDIUM"
    created_at: datetime
    allowed_business_hours: float
    deadline_at: datetime
    status: str = "OPEN" # OPEN, WARNING_75, BREACHED, RESOLVED
    is_escalated: bool = False
    escalation_reason: Optional[str] = None
    assigned_agent_id: Optional[str] = None
    target_queue: str = "general_queue"
    warning_triggered: bool = False
    breach_triggered: bool = False
    masked_summary: Optional[str] = None

class SLAManager:
    def __init__(self):
        self.tickets: Dict[str, Ticket] = {}

    def create_ticket(self, customer: str, issue: str, priority_tier: str = "MEDIUM",
                      order_id: Optional[str] = None, product: Optional[str] = None,
                      contact_details: Optional[str] = None, evidence: Optional[str] = None,
                      assigned_agent_id: Optional[str] = None, target_queue: str = "general_queue",
                      masked_summary: Optional[str] = None,
                      created_at_override: Optional[datetime] = None) -> Ticket:
        """Creates and registers a new ticket with business-hour SLA deadline."""
        now = created_at_override or time_engine.now()
        allowed_hours = config.sla_hours_map.get(priority_tier.upper(), 8.0)
        deadline = time_engine.add_business_hours(now, allowed_hours)
        ticket_id = f"TCK-{uuid.uuid4().hex[:6].upper()}"

        ticket = Ticket(
            ticket_id=ticket_id,
            customer=customer,
            order_id=order_id,
            product=product,
            issue=issue,
            contact_details=contact_details,
            evidence=evidence,
            priority_tier=priority_tier.upper(),
            created_at=now,
            allowed_business_hours=allowed_hours,
            deadline_at=deadline,
            assigned_agent_id=assigned_agent_id,
            target_queue=target_queue,
            masked_summary=masked_summary
        )
        self.tickets[ticket_id] = ticket
        audit_logger.log("INFO", f"Ticket {ticket_id} created for {customer}. Allowed SLA: {allowed_hours} business hours. Deadline: {deadline.isoformat()}")
        return ticket

    def evaluate_ticket_sla(self, ticket: Ticket, current_time: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Evaluates SLA consumption ratio strictly excluding weekends and holidays.
        Triggers 75% warning and 100% breach escalation.
        """
        now = current_time or time_engine.now()
        if ticket.status == "RESOLVED":
            return {"ticket_id": ticket.ticket_id, "status": "RESOLVED", "ratio": 0.0}

        # Calculate business seconds elapsed since ticket creation
        elapsed_biz_seconds = time_engine.calculate_business_seconds_between(ticket.created_at, now)
        total_allowed_seconds = ticket.allowed_business_hours * 3600.0
        ratio = elapsed_biz_seconds / max(total_allowed_seconds, 1.0)

        # 1. Breach Check (100%)
        if ratio >= config.sla_breach_threshold or now >= ticket.deadline_at:
            if not ticket.breach_triggered:
                ticket.status = "BREACHED"
                ticket.is_escalated = True
                ticket.breach_triggered = True
                ticket.escalation_reason = f"SLA 100% Breach: {round(ratio*100, 1)}% time consumed"
                audit_logger.log_escalation(
                    reason="SLA Breach Escalation",
                    activated_condition=f"sla_breach_100_percent (elapsed={round(elapsed_biz_seconds/3600, 2)}h / allowed={ticket.allowed_business_hours}h)",
                    conversation_summary=f"Ticket {ticket.ticket_id} ({ticket.issue}) breached SLA deadline {ticket.deadline_at.isoformat()}.",
                    details={"ticket_id": ticket.ticket_id, "ratio": round(ratio, 3)}
                )
            return {
                "ticket_id": ticket.ticket_id,
                "status": "BREACHED",
                "consumption_ratio": round(ratio, 3),
                "is_escalated": True,
                "alert": "BREACH_ESCALATED"
            }

        # 2. Warning Check (75%)
        elif ratio >= config.sla_warning_threshold:
            if not ticket.warning_triggered:
                ticket.status = "WARNING_75"
                ticket.warning_triggered = True
                audit_logger.log("WARNING", f"SLA Warning: Ticket {ticket.ticket_id} has consumed {round(ratio*100, 1)}% of allowed SLA time.")
            return {
                "ticket_id": ticket.ticket_id,
                "status": "WARNING_75",
                "consumption_ratio": round(ratio, 3),
                "is_escalated": ticket.is_escalated,
                "alert": "SLA_WARNING_75_PERCENT"
            }

        return {
            "ticket_id": ticket.ticket_id,
            "status": ticket.status,
            "consumption_ratio": round(ratio, 3),
            "is_escalated": ticket.is_escalated,
            "alert": "NORMAL"
        }

    def update_runtime_sla_policy(self, priority_tier: str, new_business_hours: float):
        """
        Dynamically modifies SLA policies at runtime and recalculates
        deadlines for all open tickets of that tier.
        """
        tier = priority_tier.upper()
        old_hours = config.sla_hours_map.get(tier, 8.0)
        config.sla_hours_map[tier] = new_business_hours
        audit_logger.log("WARNING", f"RUNTIME SLA CHANGE: Tier '{tier}' changed from {old_hours}h to {new_business_hours}h.")

        # Recalculate for all open tickets
        for ticket in self.tickets.values():
            if ticket.priority_tier == tier and ticket.status not in ["RESOLVED", "BREACHED"]:
                ticket.allowed_business_hours = new_business_hours
                ticket.deadline_at = time_engine.add_business_hours(ticket.created_at, new_business_hours)
                # Re-evaluate with updated deadline
                self.evaluate_ticket_sla(ticket)

    def evaluate_all(self, current_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Evaluates SLA status for all managed tickets."""
        results = []
        for ticket in self.tickets.values():
            results.append(self.evaluate_ticket_sla(ticket, current_time))
        return results

sla_manager = SLAManager()
