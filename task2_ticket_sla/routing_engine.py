"""
Task 2: Dynamic Agent Skill, Availability, Workload & Business Hours Routing Engine.
Handles skill-based matching, capacity balancing, after-hours dispatch, and unavailable team fallbacks.
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from core.time_engine import time_engine
from core.logger import audit_logger

class SupportAgent(BaseModel):
    agent_id: str
    name: str
    skills: List[str]
    is_online: bool = True
    current_tickets: int = 0
    max_capacity: int = 5
    is_on_call: bool = False

class RoutingResult(BaseModel):
    assigned_agent_id: Optional[str] = None
    assigned_agent_name: Optional[str] = None
    target_queue: str
    routing_strategy: str
    is_after_hours: bool
    is_team_unavailable: bool = False
    notes: Optional[str] = None

class RoutingEngine:
    def __init__(self):
        # Default agent roster
        self.agents: Dict[str, SupportAgent] = {
            "AGT-TECH-1": SupportAgent(agent_id="AGT-TECH-1", name="Alex Chen", skills=["technical", "hardware", "software"], is_online=True, current_tickets=2, is_on_call=True),
            "AGT-BILL-1": SupportAgent(agent_id="AGT-BILL-1", name="Sarah Jenkins", skills=["billing", "payments", "refunds"], is_online=True, current_tickets=1, is_on_call=False),
            "AGT-RET-1": SupportAgent(agent_id="AGT-RET-1", name="Rajesh Kumar", skills=["returns", "shipping", "logistics"], is_online=True, current_tickets=3, is_on_call=False),
            "AGT-GEN-1": SupportAgent(agent_id="AGT-GEN-1", name="Maria Garcia", skills=["general", "inquiries", "multilingual"], is_online=True, current_tickets=1, is_on_call=True),
            "AGT-ONCALL-1": SupportAgent(agent_id="AGT-ONCALL-1", name="Emergency Night Lead", skills=["technical", "billing", "general"], is_online=True, current_tickets=0, is_on_call=True)
        }

    def register_agent(self, agent: SupportAgent):
        """Adds or updates an agent in the active pool."""
        self.agents[agent.agent_id] = agent

    def set_agent_status(self, agent_id: str, is_online: bool, is_on_call: Optional[bool] = None):
        """Modifies availability at runtime (useful for unavailable team simulations)."""
        if agent_id in self.agents:
            self.agents[agent_id].is_online = is_online
            if is_on_call is not None:
                self.agents[agent_id].is_on_call = is_on_call

    def identify_required_skill(self, issue_text: str) -> str:
        """Determines required domain skill from issue description."""
        lower = (issue_text or "").lower()
        if any(w in lower for w in ["charge", "payment", "duplicate", "bill", "invoice", "refund", "card", "tax", "fee"]):
            return "billing"
        elif any(w in lower for w in ["crash", "error", "bug", "broken", "hardware", "screen", "battery", "laptop", "technical"]):
            return "technical"
        elif any(w in lower for w in ["return", "ship", "delivery", "tracking", "courier", "package", "lost"]):
            return "returns"
        return "general"

    def route_ticket(self, issue_text: str, priority_tier: str = "MEDIUM",
                     is_urgent: bool = False, required_skill_override: Optional[str] = None) -> RoutingResult:
        """
        Routes ticket using agent skills, availability, workload, and business hours.
        Gracefully handles unavailable teams and after-hours conditions.
        """
        current_time = time_engine.now()
        is_business_hours = time_engine.is_within_business_hours(current_time)
        required_skill = required_skill_override or self.identify_required_skill(issue_text)

        # After-hours handling
        if not is_business_hours:
            if is_urgent or priority_tier == "CRITICAL":
                # Look for on-call agents
                on_call_candidates = [
                    a for a in self.agents.values()
                    if a.is_on_call and a.is_online and a.current_tickets < a.max_capacity
                ]
                if on_call_candidates:
                    best_agent = min(on_call_candidates, key=lambda a: a.current_tickets)
                    best_agent.current_tickets += 1
                    return RoutingResult(
                        assigned_agent_id=best_agent.agent_id,
                        assigned_agent_name=best_agent.name,
                        target_queue="on_call_emergency_queue",
                        routing_strategy="after_hours_on_call_assignment",
                        is_after_hours=True,
                        notes=f"Routed to on-call agent {best_agent.name} for urgent after-hours resolution."
                    )
                else:
                    return RoutingResult(
                        target_queue="on_call_emergency_queue",
                        routing_strategy="after_hours_on_call_queue_unassigned",
                        is_after_hours=True,
                        is_team_unavailable=True,
                        notes="No on-call agent currently available; ticket queued in on-call priority triage."
                    )
            else:
                next_start = time_engine.get_next_business_day_start(current_time)
                return RoutingResult(
                    target_queue="scheduled_next_business_day",
                    routing_strategy="after_hours_scheduled_workday",
                    is_after_hours=True,
                    notes=f"Outside business hours. Ticket scheduled for next business day ({next_start.strftime('%Y-%m-%d %H:%M')})."
                )

        # Normal business hours routing
        matching_agents = [
            a for a in self.agents.values()
            if required_skill in a.skills and a.is_online and a.current_tickets < a.max_capacity
        ]

        # Case 1: Matching agent available
        if matching_agents:
            # Load balancing: choose agent with minimum current load
            selected_agent = min(matching_agents, key=lambda a: a.current_tickets)
            selected_agent.current_tickets += 1
            return RoutingResult(
                assigned_agent_id=selected_agent.agent_id,
                assigned_agent_name=selected_agent.name,
                target_queue=f"{required_skill}_queue",
                routing_strategy="skill_and_workload_balanced",
                is_after_hours=False,
                notes=f"Matched skill '{required_skill}' to {selected_agent.name} (active tickets: {selected_agent.current_tickets}/{selected_agent.max_capacity})."
            )

        # Case 2: Matching team is UNAVAILABLE (offline or at max capacity)
        # Attempt fallback to general pool agents who are online
        fallback_agents = [
            a for a in self.agents.values()
            if a.is_online and a.current_tickets < a.max_capacity
        ]
        if fallback_agents:
            fallback_agent = min(fallback_agents, key=lambda a: a.current_tickets)
            fallback_agent.current_tickets += 1
            audit_logger.log("WARNING", f"Team unavailable for skill '{required_skill}'. Re-routed to general agent {fallback_agent.name}.")
            return RoutingResult(
                assigned_agent_id=fallback_agent.agent_id,
                assigned_agent_name=fallback_agent.name,
                target_queue="general_overflow_queue",
                routing_strategy="fallback_general_due_to_team_unavailability",
                is_after_hours=False,
                is_team_unavailable=True,
                notes=f"Primary '{required_skill}' team unavailable. Reassigned to general support agent {fallback_agent.name}."
            )

        # Case 3: All teams completely saturated/unavailable
        audit_logger.log("ERROR", f"CRITICAL: All teams unavailable for skill '{required_skill}'! Queued in supervisor holding queue.")
        return RoutingResult(
            target_queue="supervisor_escalation_queue",
            routing_strategy="unassigned_team_unavailable",
            is_after_hours=False,
            is_team_unavailable=True,
            notes="All agent teams are currently unavailable or saturated. Ticket prioritized in supervisor queue."
        )

routing_engine = RoutingEngine()
