"""
Global Configuration for Elevance Enterprise AI Customer Support Platform.
All parameters are configurable dynamically at runtime.
"""
from typing import List, Set, Dict, Any
from pydantic import BaseModel, Field
from datetime import time, date

class SystemConfig(BaseModel):
    # Business Hours & Calendar
    business_start_hour: int = 9   # 09:00
    business_start_minute: int = 0
    business_end_hour: int = 18    # 18:00
    business_end_minute: int = 0
    business_days: List[int] = Field(default_factory=lambda: [0, 1, 2, 3, 4])  # Mon - Fri
    holidays: Set[str] = Field(default_factory=lambda: {
        "2026-01-01", # New Year
        "2026-01-26", # Republic Day
        "2026-08-15", # Independence Day
        "2026-10-02", # Gandhi Jayanti
        "2026-12-25", # Christmas
    })

    # Escalation Rules (Task 1)
    negative_escalation_minutes: float = 15.0  # 15 minutes unresolved negative conversation
    high_risk_keywords: List[str] = Field(default_factory=lambda: [
        "account compromise", "hacked", "unauthorized access", "stolen credentials",
        "duplicate payment", "charged twice", "double charged", "double debit",
        "legal action", "lawyer", "attorney", "sue", "lawsuit", "police complaint",
        "consumer court", "regulatory notice", "gdpr breach"
    ])

    # SLA Rules (Task 2)
    sla_warning_threshold: float = 0.75  # 75% consumed
    sla_breach_threshold: float = 1.0    # 100% consumed
    # Business hours allowed per priority
    sla_hours_map: Dict[str, float] = Field(default_factory=lambda: {
        "CRITICAL": 2.0,
        "HIGH": 4.0,
        "MEDIUM": 8.0,
        "LOW": 24.0
    })

    # Knowledge Base CI/CD Pipeline (Task 3)
    kb_retry_intervals_minutes: List[int] = Field(default_factory=lambda: [15, 30, 60])
    maintenance_window_start_hour: int = 1   # 01:00
    maintenance_window_end_hour: int = 5     # 05:00
    canary_health_check_minutes: float = 5.0 # Rollback if health checks fail within 5 minutes
    min_accuracy_threshold: float = 0.85
    min_grounding_threshold: float = 0.85

    # Multimodal & OCR Settings (Task 5)
    async_processing_threshold_seconds: float = 30.0
    file_retention_seconds: float = 86400.0  # 24 hours default retention
    allowed_mime_types: List[str] = Field(default_factory=lambda: [
        "image/png", "image/jpeg", "image/jpg", "image/webp", "application/pdf"
    ])

    # Multilingual & Session Settings (Task 6)
    supported_languages: List[str] = Field(default_factory=lambda: [
        "en", "hi", "es", "fr", "de", "hinglish"
    ])
    language_confidence_threshold: float = 0.60
    intent_confidence_threshold: float = 0.55
    session_inactivity_minutes: float = 30.0  # End session after 30 mins inactivity
    session_restore_window_hours: float = 24.0 # Restore summary if returning within 24h
    min_context_retention_messages: int = 10

# Global runtime configuration instance
config = SystemConfig()
