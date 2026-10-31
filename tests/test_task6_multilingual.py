"""
Unit & Integration Tests for Task 6:
Multilingual Context, Transliteration, Entity Preservation, and Session Lifecycles.
"""
import pytest
from datetime import datetime, timedelta
from core.time_engine import time_engine
from core.config import config
from task6_multilingual_context.language_manager import language_manager
from task6_multilingual_context.transliteration_normalizer import transliteration_normalizer
from task6_multilingual_context.entity_preserver import entity_preserver
from task6_multilingual_context.session_manager import session_manager
from task6_multilingual_context.orchestrator import chatbot_orchestrator

def test_multilingual_detection_and_code_switching():
    # Spanish detection
    es_res = language_manager.detect_language("Hola, necesito ayuda para cancelar mi pedido por favor.")
    assert es_res.language == "es"
    assert es_res.confidence >= 0.70

    # French detection
    fr_res = language_manager.detect_language("Bonjour, où est ma commande? Merci beaucoup.")
    assert fr_res.language == "fr"

    # Hinglish / Mixed language code switching detection
    hinglish_msg = "Mera package delay ho gaya hai and I want refund please."
    mix_res = language_manager.detect_language(hinglish_msg)
    assert mix_res.is_mixed is True
    assert mix_res.language in ["hi", "en"]

def test_transliteration_and_spelling_corrections():
    # Transliterated Hinglish normalized
    hinglish_text = "Mera order deliver nahi hua kripya refund karein."
    normalized = transliteration_normalizer.normalize_transliteration(hinglish_text)
    assert "not been delivered" in normalized
    assert "refund my payment" in normalized

    # Common spelling typos corrected
    typo_text = "I want a refud because the delivry was cancle and item brokn."
    fixed = transliteration_normalizer.correct_spelling(typo_text)
    assert "refund" in fixed
    assert "delivery" in fixed
    assert "cancel" in fixed
    assert "broken" in fixed

def test_entity_preservation():
    raw_text = "Customer Parth Biradar placed order ORD-99201 on 2026-08-14 for SKU-HEAD-001."
    protected, token_map = entity_preserver.protect_entities(raw_text)
    assert "ORD-99201" not in protected
    assert "__PRESERVED_ORDER_0__" in protected
    assert "2026-08-14" not in protected
    assert "__PRESERVED_DATE_2__" in protected or "__PRESERVED_DATE_" in protected

    # Restore entities
    restored = entity_preserver.restore_entities(protected, token_map)
    assert restored == raw_text
    assert "Parth Biradar" in restored
    assert "ORD-99201" in restored
    assert "SKU-HEAD-001" in restored

def test_user_corrected_information():
    # Customer updates / corrects order ID in same turn
    msg = "My order number is ORD-1111. Wait, sorry, actually it is ORD-9999."
    correction = transliteration_normalizer.extract_corrected_information(msg)
    assert correction["has_correction"] is True
    assert correction["field"] == "order_id"
    assert correction["original_val"] == "ORD-1111"
    assert correction["corrected_val"] == "ORD-9999"

def test_multi_tenant_session_isolation():
    # Two simultaneous customer sessions
    sess_a, _ = session_manager.get_or_create_session("customer_alice")
    sess_b, _ = session_manager.get_or_create_session("customer_bob")
    assert sess_a.session_id != sess_b.session_id

    session_manager.add_message(sess_a.session_id, role="user", content="Alice's private secret note")
    session_manager.add_message(sess_b.session_id, role="user", content="Bob's inquiry")

    alice_msgs = [t.content for t in sess_a.history]
    bob_msgs = [t.content for t in sess_b.history]
    assert "Alice's private secret note" in alice_msgs
    assert "Alice's private secret note" not in bob_msgs # Zero cross-talk leakage!

def test_context_retention_over_10_turns():
    sess, _ = session_manager.get_or_create_session("customer_charlie")
    for i in range(12):
        session_manager.add_message(sess.session_id, role="user", content=f"Message turn number {i}")
        session_manager.add_message(sess.session_id, role="assistant", content=f"Response turn {i}")
    
    # Must retain at least 10 messages
    assert len(sess.history) >= 10

def test_session_inactivity_30m_expiry_and_24h_summary_restoration():
    base_time = datetime(2026, 9, 15, 10, 0, 0)
    time_engine.set_time(base_time)

    # Customer starts session and talks about damaged headphones
    sess1, action1 = session_manager.get_or_create_session("customer_david")
    session_manager.add_message(sess1.session_id, role="user", content="My headphone headband is broken and I need an exchange.")
    session_manager.add_message(sess1.session_id, role="assistant", content="We can help you with headphone replacement.")

    # Advance time by 35 minutes (>30 min inactivity expiry)
    time_engine.advance_time(minutes=35)

    # Customer returns within 2 hours (<24h return window)
    sess2, action2 = session_manager.get_or_create_session("customer_david")
    assert action2 == "RESTORED_PREVIOUS_SUMMARY"
    assert sess2.session_id != sess1.session_id
    assert sess2.conversation_summary is not None
    assert "headphone" in sess2.conversation_summary.lower()

    # Now close session sess2, then simulate customer returning after 25 hours (>24h window)
    session_manager.close_session(sess2.session_id)
    time_engine.advance_time(hours=25)

    sess3, action3 = session_manager.get_or_create_session("customer_david")
    assert action3 == "FRESH_SESSION"

    time_engine.reset_to_real_time()
