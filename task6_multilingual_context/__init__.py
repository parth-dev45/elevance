"""
Task 6: Multilingual Session Management, Transliteration & Context Engine package.
"""
from task6_multilingual_context.language_manager import language_manager, LanguageManager, LanguageDetectionResult
from task6_multilingual_context.entity_preserver import entity_preserver, EntityPreserver
from task6_multilingual_context.transliteration_normalizer import transliteration_normalizer, TransliterationNormalizer
from task6_multilingual_context.session_manager import session_manager, SessionManager, CustomerSession, SessionTurn
from task6_multilingual_context.orchestrator import chatbot_orchestrator, ChatbotOrchestrator, BotResponse

__all__ = [
    "language_manager",
    "LanguageManager",
    "LanguageDetectionResult",
    "entity_preserver",
    "EntityPreserver",
    "transliteration_normalizer",
    "TransliterationNormalizer",
    "session_manager",
    "SessionManager",
    "CustomerSession",
    "SessionTurn",
    "chatbot_orchestrator",
    "ChatbotOrchestrator",
    "BotResponse",
]
