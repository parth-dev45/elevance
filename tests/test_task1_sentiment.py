"""
Unit & Integration Tests for Task 1:
Multilingual Sentiment Analysis, Tone Adaptation & Escalation Engine.
"""
import pytest
from datetime import datetime, timedelta
from core.time_engine import time_engine
from core.config import config
from task1_sentiment_escalation.sentiment_analyzer import sentiment_analyzer
from task1_sentiment_escalation.tone_adapter import tone_adapter
from task1_sentiment_escalation.escalation_engine import escalation_engine

def test_sarcasm_detection():
    # Outwardly positive words used in severe failure context
    msg = "Oh fantastic, my order hasn't arrived in 3 weeks, stellar customer service guys!"
    res = sentiment_analyzer.analyze_message(msg)
    assert res.is_sarcastic is True
    assert res.primary_sentiment in ["sarcastic", "frustrated", "negative"]

def test_calm_high_risk_detection():
    # Calm, polite phrasing but contains legal threat
    msg = "Good morning. Please be advised that I have informed my attorney and we will be filing a lawsuit regarding the unauthorized access."
    res = sentiment_analyzer.analyze_message(msg)
    assert "legal_threat" in res.high_risk_flags or "account_compromise" in res.high_risk_flags
    
    # Escalation engine should escalate immediately
    decision = escalation_engine.evaluate(msg, res)
    assert decision.is_escalated is True
    assert "High-risk issue detected" in decision.reason
    assert "high_risk_trigger" in decision.activated_condition
    assert decision.conversation_summary is not None

def test_duplicate_payment_high_risk():
    msg = "I noticed a duplicate payment on my credit card statement for order ORD-1234. I was charged twice."
    res = sentiment_analyzer.analyze_message(msg)
    assert "duplicate_payment" in res.high_risk_flags
    decision = escalation_engine.evaluate(msg, res)
    assert decision.is_escalated is True
    assert "Duplicate Payment" in decision.reason

def test_tone_adaptation_preserves_policy():
    policy = "Standard returns must be initiated within 14 days of delivery. Return shipping fee is $5.99."
    frustrated_tone = tone_adapter.adapt_response(policy, sentiment="frustrated")
    assert policy in frustrated_tone
    assert "frustrating" in frustrated_tone.lower()

    urgent_tone = tone_adapter.adapt_response(policy, sentiment="urgent", is_urgent=True)
    assert policy in urgent_tone
    assert "immediate action" in urgent_tone.lower()

def test_repeated_negative_messages_escalation():
    # Simulation: turn 1 negative, turn 2 negative
    history = [
        {"role": "user", "content": "The package arrived damaged and unusable.", "sentiment": "negative"},
        {"role": "assistant", "content": "I apologize. Please provide a photo.", "sentiment": "neutral"}
    ]
    curr_msg = "This is ridiculous, why are you giving me the runaround? Horrible support!"
    res = sentiment_analyzer.analyze_message(curr_msg, history=history)
    decision = escalation_engine.evaluate(curr_msg, res, history=history)
    assert decision.is_escalated is True
    assert "repeated_negative_messages_threshold" in decision.activated_condition

def test_negative_conversation_unresolved_over_15_minutes():
    # Set simulated time to a normal business hour (e.g. Wednesday 11:00 AM)
    base_time = datetime(2026, 9, 16, 11, 0, 0) # Wednesday 11 AM
    time_engine.set_time(base_time)

    first_neg_time = base_time - timedelta(minutes=16) # 16 minutes ago
    curr_msg = "Still waiting for someone to help me with this broken item."
    res = sentiment_analyzer.analyze_message(curr_msg)
    decision = escalation_engine.evaluate(
        curr_msg, res,
        history=[{"role": "user", "content": "Item broken", "sentiment": "negative"}],
        first_negative_time=first_neg_time
    )
    assert decision.is_escalated is True
    assert "unresolved_negative_duration_exceeded" in decision.activated_condition

def test_after_hours_urgent_vs_normal():
    # Set simulated time to Sunday night 22:00 (Outside business hours)
    after_hours = datetime(2026, 9, 20, 22, 0, 0) # Sunday 10 PM
    time_engine.set_time(after_hours)

    # 1. Urgent after-hours complaint -> on-call queue
    urgent_msg = "Emergency! The system crashed and our production database is down, urgent help needed!"
    res_urgent = sentiment_analyzer.analyze_message(urgent_msg)
    decision_urgent = escalation_engine.evaluate(urgent_msg, res_urgent)
    assert decision_urgent.is_escalated is True
    assert decision_urgent.target_queue == "on_call_emergency_queue"

    # 2. Normal complaint after-hours -> scheduled for next business day
    normal_msg = "I am not satisfied with the color of the t-shirt I received."
    res_normal = sentiment_analyzer.analyze_message(normal_msg)
    decision_normal = escalation_engine.evaluate(normal_msg, res_normal)
    assert decision_normal.is_escalated is True
    assert decision_normal.target_queue == "scheduled_next_business_day"
    assert decision_normal.scheduled_time is not None
    # Next business day from Sunday 10 PM is Monday 09:00 AM
    assert decision_normal.scheduled_time.weekday() == 0 # Monday
    assert decision_normal.scheduled_time.hour == 9
    assert decision_normal.scheduled_time.minute == 0

    time_engine.reset_to_real_time()
