"""
Task 1: Multilingual Sentiment and Emotion Analyzer.
Identifies: positive, neutral, negative, frustrated, urgent, sarcastic.
Analyzes current message + conversation history with confidence scoring.
Detects sarcasm, calm high-risk statements, and multilingual expressions.
"""
import re
from typing import List, Dict, Any, Tuple
from core.security import security_service

class SentimentResult:
    def __init__(self, primary_sentiment: str, confidence: float, scores: Dict[str, float],
                 is_sarcastic: bool, is_urgent: bool, high_risk_flags: List[str], detected_language: str = "en"):
        self.primary_sentiment = primary_sentiment
        self.confidence = confidence
        self.scores = scores
        self.is_sarcastic = is_sarcastic
        self.is_urgent = is_urgent
        self.high_risk_flags = high_risk_flags
        self.detected_language = detected_language

    def to_dict(self) -> Dict[str, Any]:
        return {
            "primary_sentiment": self.primary_sentiment,
            "confidence": round(self.confidence, 3),
            "scores": {k: round(v, 3) for k, v in self.scores.items()},
            "is_sarcastic": self.is_sarcastic,
            "is_urgent": self.is_urgent,
            "high_risk_flags": self.high_risk_flags,
            "detected_language": self.detected_language
        }

class SentimentAnalyzer:
    def __init__(self):
        # Multilingual Lexicons
        self.positive_keywords = {
            "en": ["great", "excellent", "awesome", "good", "thank", "thanks", "helpful", "perfect", "wonderful", "love", "resolved", "brilliant", "fantastic", "stellar"],
            "es": ["excelente", "bueno", "gracias", "perfecto", "maravilloso", "genial", "resuelto", "amable", "estupendo"],
            "fr": ["merci", "bon", "excellent", "parfait", "merveilleux", "génial", "résolu", "super", "formidable"],
            "de": ["danke", "gut", "ausgezeichnet", "perfekt", "wunderbar", "toll", "gelöst", "hervorragend"],
            "hi": ["dhanyavad", "shukriya", "accha", "badhiya", "sundar", "sahi", "dhanyavaad", "sukriya", "khush"]
        }

        self.negative_keywords = {
            "en": ["bad", "poor", "horrible", "awful", "terrible", "disappointed", "worst", "broken", "fail", "failed", "unhappy", "problem", "defect", "useless", "faulty", "dissatisfied", "not satisfied", "not happy", "not working", "not received", "didn't arrive", "delayed"],
            "es": ["malo", "horrible", "terrible", "decepcionado", "peor", "roto", "fallo", "problema", "defecto", "no satisfecho", "no funciona"],
            "fr": ["mauvais", "horrible", "terrible", "déçu", "pire", "cassé", "échoué", "problème", "défectueux", "pas satisfait", "ne fonctionne pas"],
            "de": ["schlecht", "furchtbar", "schrecklich", "enttäuscht", "kaputt", "fehlgeschlagen", "problem", "defekt", "nicht zufrieden"],
            "hi": ["kharab", "bura", "ghatiya", "bekar", "bakwas", "toota", "galat", "pareshan", "samasya", "nahi mila", "nahi aaya", "kaam nahi kar raha"]
        }

        self.frustrated_keywords = {
            "en": ["ridiculous", "fed up", "unacceptable", "waste of time", "third time", "repeatedly", "tired of", "angry", "disgusted", "scam", "shameful", "pathetic", "incompetent", "annoyed", "pissed", "sick of"],
            "es": ["ridículo", "harto", "inaceptable", "pérdida de tiempo", "estafa", "incompetente", "furioso", "enfadado"],
            "fr": ["ridicule", "marre", "inacceptable", "perte de temps", "arnaque", "incompétent", "furieux", "honteux"],
            "de": ["lächerlich", "satt", "inakzeptabel", "zeitverschwendung", "betrug", "inkompetent", "wütend", "schande"],
            "hi": ["tang aa chuka", "pareshan ho gaya", "bar bar", "dhokha", "hadd hai", "sharmnaak", "gussa", "mood kharab"]
        }

        self.urgent_keywords = {
            "en": ["urgent", "immediately", "asap", "emergency", "right now", "stranded", "critical", "hurry", "time sensitive", "at once"],
            "es": ["urgente", "inmediatamente", "asap", "emergencia", "ahora mismo", "crítico", "rápido"],
            "fr": ["urgent", "immédiatement", "urgence", "tout de suite", "critique", "vite"],
            "de": ["dringend", "sofort", "notfall", "kritisch", "schnellstmöglich"],
            "hi": ["turant", "jaldi", "emergency", "kripya jaldi", "bina deri", "aaj hi"]
        }

        # High-risk issue patterns (regardless of calm or polite phrasing!)
        self.high_risk_patterns = [
            (r"\b(compromis(ed?)|hack(ed)?|unauthorized\s+access|stolen\s+(account|card|credentials|password)|account\s+taken\s+over)\b", "account_compromise"),
            (r"\b(duplicate\s+payment|charged\s+twice|double\s+charge(d)?|double\s+debit|billed\s+twice|two\s+times\s+charged)\b", "duplicate_payment"),
            (r"\b(lawyer|attorney|legal\s+(action|notice|counsel)|sue(\b|ing)|lawsuit|court|police(\s+complaint)?|fir|consumer\s+(court|forum)|regulatory\s+complaint|gdpr\s+violation)\b", "legal_threat")
        ]

        # Sarcasm markers & incongruity patterns
        self.sarcasm_cues = [
            r"\b(oh\s+)?(great|fantastic|wonderful|brilliant|stellar|amazing|superb)\b.*(not\s+(working|arrived|received)|broke|fail|empty|waste|weeks?|days?|stolen|charged|waiting)",
            r"(love\s+how\s+you|thanks\s+for\s+nothing|stellar\s+customer\s+service|genius\s+move|bravo|clapping)",
            r"\b(wow|oh\s+wow)\b.*(\?{2,}|\!{2,})",
            r"(pure\s+perfection\b.*(not|zero|never))",
            r"kya\s+baat\s+hai.*(kharab|bekar|nahi\s+aaya)"
        ]

    def _flatten_keywords(self, kw_dict: Dict[str, List[str]]) -> List[str]:
        words = []
        for lang_words in kw_dict.values():
            words.extend(lang_words)
        return words

    def detect_high_risk(self, text: str) -> List[str]:
        """Identifies high-risk issues such as account compromise, duplicate payments, or legal action."""
        flags = []
        lower_text = text.lower()
        for pattern, risk_name in self.high_risk_patterns:
            if re.search(pattern, lower_text):
                flags.append(risk_name)
        return list(set(flags))

    def detect_sarcasm(self, text: str) -> Tuple[bool, float]:
        """
        Detects sarcastic messages where outwardly positive words are used
        in a context describing failure, delays, or severe dissatisfaction.
        """
        lower = text.lower()
        # Direct pattern checks
        for cue in self.sarcasm_cues:
            if re.search(cue, lower):
                return True, 0.88

        # Incongruence check: has strong positive words AND strong negative/frustrated words
        has_pos = any(w in lower for w in ["great", "fantastic", "wonderful", "brilliant", "stellar", "amazing", "love", "perfect"])
        has_neg = any(w in lower for w in ["broken", "fail", "empty", "hours", "weeks", "lost", "ruined", "charged", "never", "stolen", "missing", "delay"])
        has_quotes_or_exclamation = bool(re.search(r'["\']|\!{2,}|\?{2,}', text))

        if has_pos and has_neg and (has_quotes_or_exclamation or "service" in lower or "thanks" in lower):
            return True, 0.82

        return False, 0.0

    def analyze_message(self, text: str, history: List[Dict[str, str]] = None) -> SentimentResult:
        """
        Analyzes current message and optional conversation history.
        Generates probability scores across all sentiments and calculates confidence.
        """
        if not text:
            return SentimentResult("neutral", 1.0, {"neutral": 1.0}, False, False, [])

        lower = text.lower()
        high_risk_flags = self.detect_high_risk(lower)
        is_sarcastic, sarcasm_score = self.detect_sarcasm(text)

        # Count occurrences across multilingual dictionaries
        pos_count = sum(1 for w in self._flatten_keywords(self.positive_keywords) if re.search(rf"\b{re.escape(w)}\b", lower))
        neg_count = sum(1 for w in self._flatten_keywords(self.negative_keywords) if re.search(rf"\b{re.escape(w)}\b", lower))
        frust_count = sum(1 for w in self._flatten_keywords(self.frustrated_keywords) if re.search(rf"\b{re.escape(w)}\b", lower))
        urg_count = sum(1 for w in self._flatten_keywords(self.urgent_keywords) if re.search(rf"\b{re.escape(w)}\b", lower))

        # Check conversation history influence
        history_neg_count = 0
        if history:
            for turn in history[-4:]:
                msg = turn.get("content", "").lower()
                if turn.get("role") in ["user", "customer"]:
                    if any(w in msg for w in self._flatten_keywords(self.negative_keywords)) or \
                       any(w in msg for w in self._flatten_keywords(self.frustrated_keywords)):
                        history_neg_count += 1

        # Aggregate raw scores
        raw_scores = {
            "positive": float(pos_count),
            "neutral": 0.5,
            "negative": float(neg_count + (0.5 * history_neg_count)),
            "frustrated": float(frust_count * 1.5 + (0.8 * history_neg_count)),
            "urgent": float(urg_count * 1.8),
            "sarcastic": sarcasm_score * 3.0 if is_sarcastic else 0.0
        }

        # Override positive if sarcastic
        if is_sarcastic:
            raw_scores["positive"] = 0.05
            raw_scores["frustrated"] += 1.0
            raw_scores["negative"] += 1.0

        # Normalization (Softmax-like distribution)
        total = sum(raw_scores.values()) or 1.0
        scores = {k: v / total for k, v in raw_scores.items()}

        # Determine primary sentiment
        if is_sarcastic:
            primary = "sarcastic"
            confidence = max(0.85, scores["sarcastic"])
        elif raw_scores["urgent"] >= 1.5:
            primary = "urgent"
            confidence = min(0.95, scores["urgent"] + 0.3)
        elif raw_scores["frustrated"] >= 1.2:
            primary = "frustrated"
            confidence = min(0.95, scores["frustrated"] + 0.25)
        elif raw_scores["negative"] > raw_scores["positive"] and raw_scores["negative"] > 0.8:
            primary = "negative"
            confidence = min(0.95, scores["negative"] + 0.2)
        elif raw_scores["positive"] > 0:
            primary = "positive"
            confidence = min(0.95, scores["positive"] + 0.2)
        else:
            primary = "neutral"
            confidence = 0.80

        is_urgent = (primary == "urgent" or urg_count > 0 or "asap" in lower or "immediately" in lower)

        return SentimentResult(
            primary_sentiment=primary,
            confidence=confidence,
            scores=scores,
            is_sarcastic=is_sarcastic,
            is_urgent=is_urgent,
            high_risk_flags=high_risk_flags
        )

sentiment_analyzer = SentimentAnalyzer()
