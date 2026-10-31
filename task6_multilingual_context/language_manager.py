"""
Task 6: Multilingual Detection & Dynamic Code-Switching Engine.
Supports English, Hindi, Spanish, French, German, and Hinglish.
Handles mid-conversation language switching and requests clarification when confidence is low.
"""
from typing import Dict, Any, List, Tuple, Optional
import re
from core.config import config
from core.logger import audit_logger

class LanguageDetectionResult:
    def __init__(self, language: str, confidence: float, is_mixed: bool = False,
                 secondary_language: Optional[str] = None, requires_clarification: bool = False,
                 clarification_prompt: Optional[str] = None):
        self.language = language
        self.confidence = confidence
        self.is_mixed = is_mixed
        self.secondary_language = secondary_language
        self.requires_clarification = requires_clarification
        self.clarification_prompt = clarification_prompt

    def to_dict(self) -> Dict[str, Any]:
        return {
            "language": self.language,
            "confidence": round(self.confidence, 3),
            "is_mixed": self.is_mixed,
            "secondary_language": self.secondary_language,
            "requires_clarification": self.requires_clarification,
            "clarification_prompt": self.clarification_prompt
        }

class LanguageManager:
    # Characteristic vocabulary patterns for language identification
    PATTERNS = {
        "es": [r"\b(hola|por\s+favor|gracias|pedido|reembolso|cancelar|problema|cuándo|dónde|devolución|ayuda|cuenta|tarjeta|dinero)\b"],
        "fr": [r"\b(bonjour|merci|s'il\s+vous\s+pla[iî]t|commande|remboursement|annuler|probl[eè]me|o[uù]|quand|retour|aide|compte)\b"],
        "de": [r"\b(hallo|guten\s+tag|bitte|danke|bestellung|erstattung|stornieren|problem|wann|wo|rückgabe|hilfe|konto|lieferung)\b"],
        "hi_devanagari": [r"[\u0900-\u097F]+"], # Native Devanagari Hindi
        "hinglish": [r"\b(mera|meri|mere|kripya|nahi|aaya|mila|kab|tak|chahiye|paisa|wapas|karo|karein|batao|kya|kyun|bahut|kharab|samasya|haan|theek|bhai|yaar|ho|gaya|gayi|hai|hain|tha|thi|raha|rahi|kar|diya|de|do)\b"],
        "en": [r"\b(the|is|are|was|were|my|and|have|has|had|for|with|this|that|i|we|you|they|in|on|at|to|a|an|it|not|be|do|does|did|what|how|why|can|will|would|should|could|hello|hi|please|thank|thanks|order|refund|cancel|issue|problem|when|where|return|help|account|card|money|shipping|package|delay|delayed|want|item|warranty|hardware|laptop|screen)\b"]
    }

    def detect_language(self, text: str, previous_language: str = "en") -> LanguageDetectionResult:
        """
        Detects primary language, mixed-language code switching, and evaluates confidence.
        If confidence is below threshold, requests clarification.
        """
        if not text or not text.strip():
            return LanguageDetectionResult(previous_language, 0.8)

        lower = text.lower()
        counts: Dict[str, int] = {"en": 0, "es": 0, "fr": 0, "de": 0, "hi": 0}

        # Check native Hindi Devanagari
        if re.search(self.PATTERNS["hi_devanagari"][0], text):
            counts["hi"] += 5

        # Check keyword presence for each language
        for lang, regexes in self.PATTERNS.items():
            if lang == "hi_devanagari":
                continue
            for r in regexes:
                matches = re.findall(r, lower)
                if matches:
                    key = "hi" if lang == "hinglish" else lang
                    counts[key] += len(matches)

        # Count total word tokens to compute confidence
        words = re.findall(r'\b[a-zA-Z\u0900-\u097F]+\b', text)
        total_words = max(len(words), 1)

        # Determine dominant language
        sorted_langs = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        top_lang, top_score = sorted_langs[0]
        second_lang, second_score = sorted_langs[1] if len(sorted_langs) > 1 else (None, 0)

        # Mixed language detection (code switching within message e.g. Hinglish or Spanglish)
        is_mixed = False
        secondary = None
        if top_score > 0 and second_score > 0:
            if second_score >= 1 and (second_score >= top_score * 0.25 or (top_score + second_score >= 3)):
                is_mixed = True
                secondary = second_lang

        # Confidence calculation
        if top_score == 0:
            # Low confidence ambiguous input (e.g. random letters or unsupported symbols)
            confidence = 0.45
            primary_lang = previous_language
        else:
            confidence = min(0.98, round((top_score / total_words) + 0.45, 2))
            primary_lang = "hi" if top_lang == "hinglish" else top_lang

        # Confidence Threshold Check
        requires_clarification = (confidence < config.language_confidence_threshold)
        prompt = None
        if requires_clarification:
            prompt = (
                "I want to make sure I understand you perfectly. Could you please specify if you would "
                "prefer to communicate in English, Hindi, Spanish, French, or German?"
            )
            audit_logger.log("INFO", f"Low language confidence ({confidence}). Clarification prompt sent.")

        return LanguageDetectionResult(
            language=primary_lang,
            confidence=confidence,
            is_mixed=is_mixed,
            secondary_language=secondary,
            requires_clarification=requires_clarification,
            clarification_prompt=prompt
        )

language_manager = LanguageManager()
