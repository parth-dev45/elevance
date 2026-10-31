"""
Security Module: PII Masking, Prompt Injection Detection, and Role-Based Access Control (RBAC).
Protects confidential customer data and prevents adversarial exploits.
"""
import re
from typing import Dict, Any, List, Optional
from enum import Enum

class UserRole(str, Enum):
    CUSTOMER = "customer"
    AGENT = "agent"
    SUPERVISOR = "supervisor"
    ADMIN = "admin"

class SecurityService:
    # Patterns for sensitive data masking
    CREDIT_CARD_REGEX = re.compile(r'\b(?:\d[ -]*?){13,19}\b')
    EMAIL_REGEX = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b')
    PHONE_REGEX = re.compile(r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b')
    SSN_TAX_REGEX = re.compile(r'\b\d{3}-\d{2}-\d{4}\b|\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b') # US SSN + Indian PAN
    CVV_REGEX = re.compile(r'\b(?:cvv|cvc|security code)[:\s]+(\d{3,4})\b', re.IGNORECASE)

    # Prompt injection signatures
    INJECTION_PATTERNS = [
        re.compile(r"ignore\s+(all\s+)?(previous|above|prior)\s+(instructions|directives|prompts)", re.IGNORECASE),
        re.compile(r"disregard\s+(the\s+)?(previous|above|system)\s+(instructions|rules)", re.IGNORECASE),
        re.compile(r"you\s+are\s+now\s+(in\s+developer\s+mode|dan|an\s+unrestricted\s+ai)", re.IGNORECASE),
        re.compile(r"system\s*prompt\s*override", re.IGNORECASE),
        re.compile(r"<\s*script\b[^>]*>", re.IGNORECASE),
        re.compile(r"jailbreak|bypass\s+safety|drop\s+table|delete\s+from", re.IGNORECASE),
        re.compile(r"print\s+(the\s+)?(system\s+prompt|secret\s+key|confidential\s+token)", re.IGNORECASE),
        re.compile(r"base64\s+decode\s+and\s+execute", re.IGNORECASE),
    ]

    # Role permission mappings
    ROLE_PERMISSIONS = {
        UserRole.CUSTOMER: {"read_public_docs", "create_ticket", "chat"},
        UserRole.AGENT: {"read_public_docs", "read_internal_docs", "create_ticket", "view_tickets", "update_ticket", "chat"},
        UserRole.SUPERVISOR: {"read_public_docs", "read_internal_docs", "read_confidential_docs", "view_tickets", "update_ticket", "override_sla", "view_analytics", "chat"},
        UserRole.ADMIN: {"read_public_docs", "read_internal_docs", "read_confidential_docs", "manage_kb", "publish_kb", "rollback_kb", "view_tickets", "update_ticket", "override_sla", "view_analytics", "chat"}
    }

    @classmethod
    def mask_pii(cls, text: str) -> str:
        """Masks credit cards, emails, phone numbers, CVV, and IDs with redacted tokens."""
        if not text:
            return text
        
        # Mask Credit Cards (keep last 4 digits if possible)
        def cc_repl(match):
            digits = re.sub(r'\D', '', match.group(0))
            if len(digits) >= 13:
                return f"[CARD_REDACTED_****{digits[-4:]}]"
            return match.group(0)

        masked = cls.CREDIT_CARD_REGEX.sub(cc_repl, text)

        # Mask CVV
        masked = cls.CVV_REGEX.sub("cvv: [CVV_MASKED]", masked)

        # Mask Emails: j***@example.com
        def email_repl(match):
            m = match.group(0)
            user, domain = m.split("@", 1)
            masked_user = user[0] + "***" if len(user) > 1 else "***"
            return f"{masked_user}@{domain}"
        masked = cls.EMAIL_REGEX.sub(email_repl, masked)

        # Mask Phone numbers
        masked = cls.PHONE_REGEX.sub("[PHONE_REDACTED]", masked)

        # Mask SSN / PAN
        masked = cls.SSN_TAX_REGEX.sub("[ID_REDACTED]", masked)

        return masked

    @classmethod
    def detect_prompt_injection(cls, text: str) -> tuple[bool, str]:
        """Detects malicious prompt injection attempts in input text or documents."""
        if not text:
            return False, ""
        for pattern in cls.INJECTION_PATTERNS:
            match = pattern.search(text)
            if match:
                return True, f"Detected malicious pattern: '{match.group(0)}'"
        return False, ""

    @classmethod
    def check_permission(cls, role: UserRole, permission: str) -> bool:
        """Verifies if the given role has the requested permission."""
        perms = cls.ROLE_PERMISSIONS.get(role, set())
        return permission in perms

    @classmethod
    def generate_masked_handoff_summary(cls, summary: str, customer_name: str, order_id: str) -> str:
        """Formats a clean, secure handoff summary with sensitive details protected."""
        sanitized = cls.mask_pii(summary)
        return (
            f"=== AGENT HANDOFF SUMMARY ===\n"
            f"Customer: {customer_name}\n"
            f"Reference: {order_id}\n"
            f"Summary & Context:\n{sanitized}\n"
            f"============================="
        )

security_service = SecurityService()
