"""
Unit & Integration Tests for Task 2:
Structured Ticket Generation, Dynamic Routing, SLA Manager, and Clustering.
"""
import pytest
from datetime import datetime, timedelta
from core.time_engine import time_engine
from core.config import config
from task2_ticket_sla.entity_extractor import entity_extractor
from task2_ticket_sla.priority_calculator import priority_calculator
from task2_ticket_sla.routing_engine import routing_engine, SupportAgent
from task2_ticket_sla.sla_manager import sla_manager
from task2_ticket_sla.ticket_clusterer import ticket_clusterer

def test_entity_extraction_and_missing_prompt():
    text = "My name is John Doe and my phone is 415-555-2671. I ordered a laptop with order ORD-99281, and the screen is completely cracked. I have attached the invoice."
    entities = entity_extractor.extract(text)
    assert entities.customer == "John Doe"
    assert entities.order_id == "ORD-99281"
    assert entities.product.lower() == "laptop"
    assert "screen is completely cracked" in entities.issue
    assert entities.evidence is not None
    assert entities.contact_details == "415-555-2671"
    assert entities.is_complete is True
    assert entities.clarification_prompt is None

    # Test missing mandatory field (no contact or customer name)
    incomplete_text = "I have an issue with order ORD-12345, the package is missing."
    inc_entities = entity_extractor.extract(incomplete_text)
    assert inc_entities.is_complete is False
    assert "customer name" in inc_entities.missing_fields
    assert "contact details (email or phone)" in inc_entities.missing_fields
    assert inc_entities.clarification_prompt is not None

def test_priority_calculation():
    # Critical high-risk case
    crit = priority_calculator.calculate_priority(
        issue_text="Unauthorized access and duplicate payment detected on my account",
        sentiment="frustrated",
        is_urgent=True,
        waiting_time_hours=4.0,
        customer_tier="enterprise",
        high_risk_flags=["account_compromise", "duplicate_payment"],
        is_escalated=True
    )
    assert crit["tier"] == "CRITICAL"
    assert crit["composite_score"] >= 3.1

    # Low priority routine inquiry
    low = priority_calculator.calculate_priority(
        issue_text="General question about warranty duration and catalog items",
        sentiment="neutral",
        waiting_time_hours=0.0,
        customer_tier="standard"
    )
    assert low["tier"] in ["LOW", "MEDIUM"]

def test_routing_skill_and_unavailable_team():
    # Set simulated time to a weekday 11:00 AM (business hours)
    time_engine.set_time(datetime(2026, 9, 16, 11, 0, 0))

    # Billing skill test
    bill_route = routing_engine.route_ticket("I need a refund for a duplicate charge on my credit card")
    assert bill_route.target_queue == "billing_queue"
    assert bill_route.is_after_hours is False

    # Simulate UNAVAILABLE team scenario: make technical agents offline
    routing_engine.set_agent_status("AGT-TECH-1", is_online=False)
    routing_engine.set_agent_status("AGT-ONCALL-1", is_online=False)
    tech_route = routing_engine.route_ticket("Laptop screen is black and hardware crashed")
    assert tech_route.is_team_unavailable is True
    assert tech_route.target_queue in ["general_overflow_queue", "supervisor_escalation_queue"]

    # Restore tech agent online status
    routing_engine.set_agent_status("AGT-TECH-1", is_online=True)
    routing_engine.set_agent_status("AGT-ONCALL-1", is_online=True)

def test_sla_weekend_holiday_exclusion_warning_and_breach():
    # Friday 17:00 (1 hour before close of business at 18:00)
    friday_5pm = datetime(2026, 9, 18, 17, 0, 0) # Friday
    time_engine.set_time(friday_5pm)

    # Create a 2-hour SLA ticket
    ticket = sla_manager.create_ticket(
        customer="Alice Smith",
        issue="Payment error",
        priority_tier="CRITICAL", # 2.0 business hours allowed
        created_at_override=friday_5pm
    )
    # The 2 business hours: 1 hour on Friday (17:00 to 18:00),
    # Saturday & Sunday are SKIPPED,
    # Remaining 1 hour must be Monday 09:00 to 10:00 AM!
    assert ticket.deadline_at.weekday() == 0 # Monday
    assert ticket.deadline_at.hour == 10
    assert ticket.deadline_at.minute == 0

    # Advance time to Monday 09:46 AM (Friday 1h + Monday 46 min = 1h 46min = 106 mins / 120 mins = 88% consumed -> >75% WARNING)
    monday_warning_time = datetime(2026, 9, 21, 9, 46, 0)
    time_engine.set_time(monday_warning_time)
    eval_warning = sla_manager.evaluate_ticket_sla(ticket, current_time=monday_warning_time)
    assert eval_warning["status"] == "WARNING_75"
    assert eval_warning["consumption_ratio"] >= 0.75
    assert eval_warning["alert"] == "SLA_WARNING_75_PERCENT"

    # Advance time to Monday 10:05 AM (Exceeded 2 hours -> BREACH)
    monday_breach_time = datetime(2026, 9, 21, 10, 5, 0)
    time_engine.set_time(monday_breach_time)
    eval_breach = sla_manager.evaluate_ticket_sla(ticket, current_time=monday_breach_time)
    assert eval_breach["status"] == "BREACHED"
    assert eval_breach["is_escalated"] is True
    assert eval_breach["alert"] == "BREACH_ESCALATED"

    time_engine.reset_to_real_time()

def test_runtime_change_to_sla_conditions():
    # Ticket created with standard 8-hour medium SLA
    now = datetime(2026, 9, 16, 9, 0, 0)
    time_engine.set_time(now)
    ticket = sla_manager.create_ticket(customer="Bob", issue="Change shipping address", priority_tier="MEDIUM")
    assert ticket.allowed_business_hours == 8.0

    # Dynamic change at runtime: reduce MEDIUM tier to 4.0 hours
    sla_manager.update_runtime_sla_policy("MEDIUM", 4.0)
    assert config.sla_hours_map["MEDIUM"] == 4.0
    assert ticket.allowed_business_hours == 4.0
    assert ticket.deadline_at == datetime(2026, 9, 16, 13, 0, 0)

    # Revert back
    sla_manager.update_runtime_sla_policy("MEDIUM", 8.0)
    time_engine.reset_to_real_time()

def test_ticket_duplicate_detection_and_clustering():
    ticket1 = sla_manager.create_ticket(customer="Eve", order_id="ORD-5544", issue="Package delayed for 2 weeks", priority_tier="MEDIUM")
    
    # Same order, duplicate complaint
    is_dup, orig_id = ticket_clusterer.detect_duplicate(
        candidate_issue="My delivery is still delayed, package not arrived",
        customer="Eve",
        order_id="ORD-5544",
        active_tickets=[ticket1]
    )
    assert is_dup is True
    assert orig_id == ticket1.ticket_id

    # Grouping related vs unrelated
    ticket2 = sla_manager.create_ticket(customer="Charlie", order_id="ORD-9999", issue="Laptop screen broken", priority_tier="HIGH")
    ticket3 = sla_manager.create_ticket(customer="David", order_id="ORD-8888", issue="Laptop screen flickering defective", priority_tier="HIGH")
    ticket4 = sla_manager.create_ticket(customer="Frank", order_id="ORD-7777", issue="Billed twice on credit card", priority_tier="CRITICAL")

    clusters = ticket_clusterer.group_and_separate_issues([ticket2, ticket3, ticket4])
    # Screen issues should cluster together, while credit card billing remains in separate cluster
    assert len(clusters) >= 2

def test_masked_handoff_summary():
    ticket = sla_manager.create_ticket(
        customer="Jane Doe",
        order_id="ORD-7788",
        issue="Payment card 4111-2222-3333-4444 was charged twice. Email is jane.doe@example.com",
        contact_details="jane.doe@example.com, phone: 415-555-9988",
        priority_tier="CRITICAL"
    )
    summary = ticket_clusterer.generate_masked_handoff_summary(ticket)
    # Masked verification
    assert "4111-2222-3333-4444" not in summary
    assert "CARD_REDACTED" in summary
    assert "jane.doe@example.com" not in summary
    assert "j***@example.com" in summary
    assert "415-555-9988" not in summary
    assert "PHONE_REDACTED" in summary
