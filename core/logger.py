"""
Telemetry, Metrics & Structured Audit Logging.
Automatically applies PII masking to all log messages and records performance events.
"""
import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime
from core.time_engine import time_engine
from core.security import security_service

class AuditLogger:
    def __init__(self):
        self.logger = logging.getLogger("elevance_audit")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

        # In-memory structured telemetry store for observability dashboard
        self.events = []
        self.escalations = []
        self.metrics = {
            "total_requests": 0,
            "total_errors": 0,
            "escalations_count": 0,
            "latencies_ms": [],
            "confidences": []
        }

    def log(self, level: str, message: str, context: Optional[Dict[str, Any]] = None):
        """Logs an event with PII masking."""
        safe_msg = security_service.mask_pii(message)
        payload = {
            "timestamp": time_engine.now().isoformat(),
            "level": level,
            "message": safe_msg,
            "context": context or {}
        }
        self.events.append(payload)
        log_str = f"{safe_msg} | Context: {json.dumps(context or {})}"
        if level == "DEBUG":
            self.logger.debug(log_str)
        elif level == "WARNING":
            self.logger.warning(log_str)
        elif level == "ERROR":
            self.logger.error(log_str)
            self.metrics["total_errors"] += 1
        else:
            self.logger.info(log_str)

    def log_escalation(self, reason: str, activated_condition: str, conversation_summary: str, details: Optional[Dict[str, Any]] = None):
        """Records an escalation with reason, activated condition, and summary."""
        escalation_record = {
            "timestamp": time_engine.now().isoformat(),
            "reason": reason,
            "activated_condition": activated_condition,
            "summary": security_service.mask_pii(conversation_summary),
            "details": details or {}
        }
        self.escalations.append(escalation_record)
        self.metrics["escalations_count"] += 1
        self.log("WARNING", f"ESCALATION ACTIVATED: {reason} | Condition: {activated_condition}", escalation_record)
        return escalation_record

    def record_metric(self, latency_ms: float, confidence: Optional[float] = None, is_error: bool = False):
        """Records performance metrics for observability."""
        self.metrics["total_requests"] += 1
        if is_error:
            self.metrics["total_errors"] += 1
        self.metrics["latencies_ms"].append(latency_ms)
        if len(self.metrics["latencies_ms"]) > 1000:
            self.metrics["latencies_ms"].pop(0)
        if confidence is not None:
            self.metrics["confidences"].append(confidence)
            if len(self.metrics["confidences"]) > 1000:
                self.metrics["confidences"].pop(0)

    def get_summary_metrics(self) -> Dict[str, Any]:
        """Calculates current running performance metrics."""
        latencies = self.metrics["latencies_ms"]
        confidences = self.metrics["confidences"]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
        avg_confidence = sum(confidences) / len(confidences) if confidences else 1.0
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0.0

        return {
            "total_requests": self.metrics["total_requests"],
            "total_errors": self.metrics["total_errors"],
            "escalations_count": self.metrics["escalations_count"],
            "avg_latency_ms": round(avg_latency, 2),
            "p95_latency_ms": round(p95_latency, 2),
            "avg_confidence": round(avg_confidence, 2),
            "escalation_rate": round(self.metrics["escalations_count"] / max(self.metrics["total_requests"], 1), 4),
            "error_rate": round(self.metrics["total_errors"] / max(self.metrics["total_requests"], 1), 4)
        }

audit_logger = AuditLogger()
