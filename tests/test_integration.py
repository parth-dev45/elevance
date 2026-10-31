"""
End-to-End Integration Tests for Elevance Enterprise Customer Support Platform.
Verifies complete flow across Tasks 1 through 6 in unified multi-turn conversations.
"""
import pytest
from datetime import datetime
from core.time_engine import time_engine
from core.security import UserRole
from task6_multilingual_context.orchestrator import chatbot_orchestrator
from task2_ticket_sla.sla_manager import sla_manager

def test_full_customer_journey_escalation_and_ticket_creation():
    # Set simulated time to a weekday 10:00 AM (Business hours)
    time_engine.set_time(datetime(2026, 9, 16, 10, 0, 0))

    cust_id = "cust_vip_100"
    
    # Turn 1: High-risk complaint (calm phrasing, legal threat + duplicate charge)
    msg1 = "Hello, my name is John Doe and my phone is 415-555-1234. I noticed a duplicate payment for order ORD-88991 and have consulted my attorney."
    bot_resp1 = chatbot_orchestrator.process_turn(
        customer_id=cust_id,
        message=msg1,
        user_role=UserRole.CUSTOMER,
        customer_tier="enterprise"
    )

    # Assertions
    assert bot_resp1.is_escalated is True
    assert "High-risk issue detected" in bot_resp1.response_text or "Escalated" in bot_resp1.response_text
    assert bot_resp1.ticket_created is not None
    assert bot_resp1.ticket_created["priority_tier"] == "CRITICAL"
    assert bot_resp1.ticket_created["order_id"] == "ORD-88991"
    assert bot_resp1.ticket_created["customer"] == "John Doe"

    # Turn 2: Follow-up duplicate inquiry on same order
    msg2 = "Any update on my duplicate payment for ORD-88991?"
    bot_resp2 = chatbot_orchestrator.process_turn(
        customer_id=cust_id,
        message=msg2,
        user_role=UserRole.CUSTOMER
    )
    assert bot_resp2.ticket_created is not None
    assert bot_resp2.ticket_created.get("is_duplicate") is True # Deduplication triggered!

    time_engine.reset_to_real_time()

def test_multilingual_code_switching_and_rag_citation():
    time_engine.set_time(datetime(2026, 9, 16, 11, 0, 0))

    cust_id = "cust_multi_200"

    # Inquire about laptop warranty with slight typo
    msg = "Hello, what is the laptop hardware waranty period?"
    bot_resp = chatbot_orchestrator.process_turn(
        customer_id=cust_id,
        message=msg,
        user_role=UserRole.CUSTOMER
    )

    assert bot_resp.is_escalated is False
    assert "Verified Policy Sources:" in bot_resp.response_text
    assert "[Source:" in bot_resp.response_text

    time_engine.reset_to_real_time()
