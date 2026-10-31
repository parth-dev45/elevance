"""
Task 1: Sentiment Analysis & Escalation Engine package.
"""
from task1_sentiment_escalation.sentiment_analyzer import sentiment_analyzer, SentimentAnalyzer, SentimentResult
from task1_sentiment_escalation.tone_adapter import tone_adapter, ToneAdapter
from task1_sentiment_escalation.escalation_engine import escalation_engine, EscalationEngine, EscalationDecision

__all__ = [
    "sentiment_analyzer",
    "SentimentAnalyzer",
    "SentimentResult",
    "tone_adapter",
    "ToneAdapter",
    "escalation_engine",
    "EscalationEngine",
    "EscalationDecision",
]
