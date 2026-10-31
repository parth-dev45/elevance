"""
Task 6: Transliteration Normalizer, Spelling Corrector, Multi-Request Decomposer,
and Information Correction Handler.
"""
import re
from typing import List, Dict, Any, Tuple, Optional

class TransliterationNormalizer:
    # Common support typo correction dictionary
    TYPO_CORRECTIONS = {
        "refud": "refund",
        "refun": "refund",
        "cancle": "cancel",
        "canceld": "cancelled",
        "delivry": "delivery",
        "delvery": "delivery",
        "waranty": "warranty",
        "warenty": "warranty",
        "brokn": "broken",
        "damagd": "damaged",
        "shippng": "shipping",
        "pakage": "package",
        "chargd": "charged",
        "doubel": "double",
        "invoce": "invoice",
        "adress": "address"
    }

    # Common Hinglish phrases mapped to normalized English equivalents
    HINGLISH_TRANSLITERATIONS = [
        (r"\bmera\s+order\s+deliver\s+nahi\s+hua\b", "my order has not been delivered"),
        (r"\b(kripya\s+)?(refund|paisa\s+wapas)\s+(karo|karein|chahiye)\b", "please refund my payment"),
        (r"\bkab\s+tak\s+aayega\b", "when will it arrive delivery tracking"),
        (r"\b(bahut\s+)?kharab\s+(product|item|service)\s+(hai|mila)\b", "received damaged broken defective item"),
        (r"\bsamasya\s+aa\s+rahi\s+hai\b", "I am facing an issue"),
        (r"\bmera\s+account\s+hack\s+ho\s+gaya\b", "my account has been compromised unauthorized access"),
        (r"\bdo\s+baar\s+(paise\s+kat\s+gaye|charge\s+hua)\b", "charged twice duplicate payment"),
    ]

    # Correction indicators
    CORRECTION_CUES = re.compile(
        r'\b(?:wait|sorry|actually|correction|i meant|no wait|galti se|actually wait|instead of)\b[:\s,]*',
        re.IGNORECASE
    )

    def normalize_transliteration(self, text: str) -> str:
        """Translates common Hinglish transliterated phrases to normalized semantic text."""
        normalized = text
        for pat, replacement in self.HINGLISH_TRANSLITERATIONS:
            normalized = re.sub(pat, replacement, normalized, flags=re.IGNORECASE)
        return normalized

    def correct_spelling(self, text: str) -> str:
        """Fixes common customer service typos while leaving valid words and entities intact."""
        words = text.split()
        corrected_words = []
        for w in words:
            # Strip punctuation for lookup
            clean = re.sub(r'[^\w]', '', w.lower())
            if clean in self.TYPO_CORRECTIONS:
                fixed = self.TYPO_CORRECTIONS[clean]
                corrected_words.append(w.lower().replace(clean, fixed))
            else:
                corrected_words.append(w)
        return " ".join(corrected_words)

    def decompose_multiple_requests(self, text: str) -> List[str]:
        """
        Decomposes compound messages with multiple requests into distinct sub-tasks.
        E.g. 'I want a refund for ORD-1111 and also please change my address to 123 Main St.'
        """
        split_pattern = re.compile(r'\b(?:and\s+also|as\s+well\s+as|plus\s+also|aur\s+bhi|y\s+adem[aá]s)\b|(?<=[.!?])\s+(?=[A-Z])', re.IGNORECASE)
        parts = [p.strip() for p in split_pattern.split(text) if p and len(p.strip()) > 5]
        return parts if len(parts) > 1 else [text]

    def extract_corrected_information(self, text: str) -> Dict[str, Any]:
        """
        Handles statements where customer provides information and then immediately corrects it.
        E.g. 'My order number is ORD-1111. Wait, sorry, actually it is ORD-9999.'
        Returns: { 'original_val': Optional[str], 'corrected_val': Optional[str], 'has_correction': bool }
        """
        has_correction = bool(self.CORRECTION_CUES.search(text))
        if not has_correction:
            return {"has_correction": False}

        # Look for two order IDs or two values separated by a correction cue
        order_matches = re.findall(r'\b[A-Za-z0-9]{3,5}-\d{4,8}\b', text)
        if len(order_matches) >= 2:
            return {
                "has_correction": True,
                "field": "order_id",
                "original_val": order_matches[0],
                "corrected_val": order_matches[-1] # The latest one after the correction cue
            }

        # Check split around correction cue
        parts = self.CORRECTION_CUES.split(text)
        if len(parts) >= 2:
            return {
                "has_correction": True,
                "pre_correction": parts[0].strip(),
                "corrected_clause": parts[1].strip()
            }

        return {"has_correction": True}

transliteration_normalizer = TransliterationNormalizer()
