"""
Task 3: Production Observability & Telemetry Service.
Monitors latency, failures, confidence scores, and escalations.
Aggregates operational metrics for reporting and dashboard visualization.
"""
from typing import Dict, Any, List
from core.logger import audit_logger
from core.time_engine import time_engine

class ObservabilityService:
    def __init__(self):
        pass

    def get_dashboard_metrics(self) -> Dict[str, Any]:
        """Returns comprehensive real-time metrics for UI and health dashboards."""
        summary = audit_logger.get_summary_metrics()
        recent_escalations = audit_logger.escalations[-10:]
        recent_events = audit_logger.events[-20:]

        return {
            "current_time": time_engine.now().isoformat(),
            "metrics": summary,
            "recent_escalations": recent_escalations,
            "recent_audit_logs": recent_events
        }

    def record_chat_latency(self, latency_ms: float, confidence: float, is_error: bool = False):
        """Records latency and confidence of individual chat interactions."""
        audit_logger.record_metric(latency_ms=latency_ms, confidence=confidence, is_error=is_error)

observability_service = ObservabilityService()
