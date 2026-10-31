"""
Task 2: Structured Entity Extractor.
Extracts customer, order, product, issue, evidence, and contact details from conversation.
Identifies missing mandatory information and generates clarification prompts.
"""
import re
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from core.security import security_service

class ExtractedEntities(BaseModel):
    customer: Optional[str] = None
    order_id: Optional[str] = None
    product: Optional[str] = None
    issue: Optional[str] = None
    evidence: Optional[str] = None
    contact_details: Optional[str] = None
    missing_fields: List[str] = Field(default_factory=list)
    is_complete: bool = True
    clarification_prompt: Optional[str] = None

class EntityExtractor:
    ORDER_REGEX = re.compile(r'\border\b(?:\s*(?:id|#|no|number))?[:\s]+([A-Za-z0-9\-]+)|\b([A-Za-z]{2,6}-\d{3,8}|#\d{4,8})\b', re.IGNORECASE)
    EMAIL_REGEX = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b')
    PHONE_REGEX = re.compile(r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b')
    PRODUCT_PATTERNS = [
        re.compile(r'(?:ordered|bought|purchased|received)\s+(?:a|an|the)?\s*([A-Za-z0-9\-]+)', re.IGNORECASE),
        re.compile(r'(?:product|item|model)[:\s]+([A-Za-z0-9\s\-]+?)(?:\.|\,|$|\n)', re.IGNORECASE),
        re.compile(r'\b(laptop|macbook|iphone|ipad|tablet|headphones|headphone|keyboard|monitor|smartwatch|t-shirt|shoes|printer|camera)\b', re.IGNORECASE),
        re.compile(r'\b(phone)\b', re.IGNORECASE)
    ]
    CUSTOMER_PATTERNS = [
        re.compile(r'(?:my name is|i am|name[:\s]+)\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', re.IGNORECASE),
        re.compile(r'(?:this is)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', re.IGNORECASE)
    ]
    EVIDENCE_PATTERNS = [
        re.compile(r'\b(invoice|screenshot|photo|receipt|tracking\s*(?:id|#|number)|error\s*(?:code)?\s*[:\s]*[A-Z0-9_\-]+)\b', re.IGNORECASE)
    ]

    def extract(self, text: str, history: Optional[List[Dict[str, Any]]] = None,
                known_customer: Optional[str] = None) -> ExtractedEntities:
        """
        Extracts structured ticket fields across current message and full context.
        Verifies presence of mandatory fields.
        """
        combined_text = text
        if history:
            history_snippets = [t.get("content", "") for t in history]
            combined_text = " \n ".join(history_snippets + [text])

        # 1. Customer
        customer = known_customer
        if not customer:
            for pat in self.CUSTOMER_PATTERNS:
                match = pat.search(combined_text)
                if match:
                    customer = match.group(1).strip()
                    break

        # 2. Order ID
        order_id = None
        order_match = self.ORDER_REGEX.search(combined_text)
        if order_match:
            val = order_match.group(1) or order_match.group(2)
            if val:
                order_id = val.strip()

        # 3. Product
        product = None
        for pat in self.PRODUCT_PATTERNS:
            match = pat.search(combined_text)
            if match:
                product = match.group(1).strip()
                break

        # 4. Evidence
        evidence = None
        for pat in self.EVIDENCE_PATTERNS:
            match = pat.search(combined_text)
            if match:
                evidence = match.group(0).strip()
                break

        # 5. Contact Details (Email or Phone)
        contact = None
        email_match = self.EMAIL_REGEX.search(combined_text)
        if email_match:
            contact = email_match.group(0)
        else:
            phone_match = self.PHONE_REGEX.search(combined_text)
            if phone_match:
                contact = phone_match.group(0)

        # 6. Issue Summary
        # Use main sentence describing the problem
        issue = None
        issue_cues = ["broken", "cracked", "damaged", "defective", "faulty", "not working", "delayed", "missing", "charged twice", "refund", "return", "cancel", "error", "hack", "compromise", "shattered", "failed"]
        sentences = re.split(r'[\.\n\!]+', text)
        for s in sentences:
            if any(cue in s.lower() for cue in issue_cues):
                issue = s.strip()
                break
        if not issue and len(text.strip()) > 0:
            issue = text.strip()

        # Check mandatory fields: customer, issue, contact_details
        missing = []
        if not customer:
            missing.append("customer name")
        if not issue:
            missing.append("issue description")
        if not contact:
            missing.append("contact details (email or phone)")

        # If order-related keywords present, order_id is mandatory
        if any(w in combined_text.lower() for w in ["order", "shipment", "delivery", "package", "bought"]) and not order_id:
            missing.append("order ID")

        is_complete = (len(missing) == 0)
        prompt = None
        if not is_complete:
            prompt = (
                f"To help us resolve your request quickly, could you please provide your: "
                f"{', '.join(missing)}?"
            )

        return ExtractedEntities(
            customer=customer,
            order_id=order_id,
            product=product,
            issue=issue,
            evidence=evidence,
            contact_details=contact,
            missing_fields=missing,
            is_complete=is_complete,
            clarification_prompt=prompt
        )

entity_extractor = EntityExtractor()
