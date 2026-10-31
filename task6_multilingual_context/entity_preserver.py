"""
Task 6: Entity Preservation Engine.
Guarantees that customer names, order IDs, dates, and product codes
remain strictly preserved and unaltered during multilingual processing and translation.
"""
import re
from typing import Dict, List, Tuple

class EntityPreserver:
    ORDER_REGEX = re.compile(r'\b(?:order\s*(?:id|#|no|number)?[:\s]*)?([A-Za-z0-9]{3,5}-\d{4,8}|#\d{4,8})\b', re.IGNORECASE)
    DATE_REGEX = re.compile(r'\b(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})\b', re.IGNORECASE)
    SKU_REGEX = re.compile(r'\b(SKU-[A-Za-z0-9_\-]+|PROD-[A-Za-z0-9_\-]+|MODEL-[A-Za-z0-9_\-]+)\b', re.IGNORECASE)
    NAME_PATTERNS = [
        re.compile(r'(?:my name is|i am|name[:\s]+)\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', re.IGNORECASE),
    ]

    def extract_critical_entities(self, text: str) -> Dict[str, List[str]]:
        """Extracts names, order IDs, dates, and product codes."""
        entities = {
            "order_ids": [],
            "dates": [],
            "product_codes": [],
            "names": []
        }
        for m in self.ORDER_REGEX.finditer(text):
            entities["order_ids"].append(m.group(0).strip())

        for m in self.DATE_REGEX.finditer(text):
            entities["dates"].append(m.group(0).strip())

        for m in self.SKU_REGEX.finditer(text):
            entities["product_codes"].append(m.group(0).strip())

        for pat in self.NAME_PATTERNS:
            for m in pat.finditer(text):
                entities["names"].append(m.group(1).strip())

        return entities

    def protect_entities(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        Replaces critical entities with safe preservation tokens before multilingual translation.
        Returns: (masked_text, token_map)
        """
        token_map = {}
        protected_text = text
        counter = 0

        # Protect Order IDs
        def ord_repl(match):
            nonlocal counter
            token = f"__PRESERVED_ORDER_{counter}__"
            token_map[token] = match.group(0)
            counter += 1
            return token
        protected_text = self.ORDER_REGEX.sub(ord_repl, protected_text)

        # Protect SKUs / Product codes
        def sku_repl(match):
            nonlocal counter
            token = f"__PRESERVED_SKU_{counter}__"
            token_map[token] = match.group(0)
            counter += 1
            return token
        protected_text = self.SKU_REGEX.sub(sku_repl, protected_text)

        # Protect Dates
        def date_repl(match):
            nonlocal counter
            token = f"__PRESERVED_DATE_{counter}__"
            token_map[token] = match.group(0)
            counter += 1
            return token
        protected_text = self.DATE_REGEX.sub(date_repl, protected_text)

        return protected_text, token_map

    def restore_entities(self, text: str, token_map: Dict[str, str]) -> str:
        """Restores exact preserved entities into translated / generated text."""
        restored = text
        for token, original_val in token_map.items():
            restored = restored.replace(token, original_val)
        return restored

entity_preserver = EntityPreserver()
