"""
Task 2: Multi-Factor Priority Calculator.
Computes ticket priority using severity, sentiment, waiting time, customer impact, and SLA rules.
Maps composite score to CRITICAL, HIGH, MEDIUM, LOW tiers.
"""
from typing import Dict, Any, Optional

class PriorityCalculator:
    def __init__(self):
        self.severity_keywords = {
            "critical": ["outage", "system down", "compromise", "hacked", "stolen", "duplicate payment", "lawsuit", "attorney", "fraud", "emergency"],
            "high": ["broken", "damaged", "wrong item", "defective", "charged twice", "cannot access", "refund"],
            "medium": ["delay", "delayed", "late", "where is", "tracking", "change address", "status"],
            "low": ["question", "inquiry", "how to", "info", "information", "catalog"]
        }

    def determine_severity(self, issue_text: str, high_risk_flags: list = None) -> float:
        """Evaluates issue text to calculate severity factor (1.0 to 4.0)."""
        if high_risk_flags:
            return 4.0
        text_lower = (issue_text or "").lower()
        for kw in self.severity_keywords["critical"]:
            if kw in text_lower:
                return 4.0
        for kw in self.severity_keywords["high"]:
            if kw in text_lower:
                return 3.0
        for kw in self.severity_keywords["medium"]:
            if kw in text_lower:
                return 2.0
        return 1.0

    def calculate_priority(self,
                           issue_text: str,
                           sentiment: str = "neutral",
                           is_urgent: bool = False,
                           waiting_time_hours: float = 0.0,
                           customer_tier: str = "standard",
                           high_risk_flags: list = None,
                           is_escalated: bool = False) -> Dict[str, Any]:
        """
        Calculates composite priority score and assigned priority tier.
        Returns: { 'tier': 'CRITICAL'|'HIGH'|'MEDIUM'|'LOW', 'score': float, 'factors': dict }
        """
        # Factor 1: Severity (1.0 to 4.0)
        sev_score = self.determine_severity(issue_text, high_risk_flags)

        # Factor 2: Sentiment (0.5 to 4.0)
        sent_map = {
            "urgent": 4.0,
            "frustrated": 3.5,
            "sarcastic": 3.2,
            "negative": 2.5,
            "neutral": 1.0,
            "positive": 0.5
        }
        sent_score = sent_map.get(sentiment.lower(), 1.0)
        if is_urgent:
            sent_score = max(sent_score, 3.8)

        # Factor 3: Waiting Time (1.0 to 4.0)
        if waiting_time_hours >= 8.0:
            wait_score = 4.0
        elif waiting_time_hours >= 4.0:
            wait_score = 3.0
        elif waiting_time_hours >= 1.5:
            wait_score = 2.0
        else:
            wait_score = 1.0

        # Factor 4: Customer Impact / Tier (1.0 to 4.0)
        tier_map = {
            "vip": 4.0,
            "enterprise": 4.0,
            "premium": 3.0,
            "business": 2.5,
            "standard": 1.5
        }
        impact_score = tier_map.get(customer_tier.lower(), 1.5)

        # Factor 5: SLA / Escalation rules factor
        sla_factor = 4.0 if is_escalated else 2.0

        # Weighted calculation
        composite = (
            (sev_score * 0.35) +
            (sent_score * 0.20) +
            (wait_score * 0.15) +
            (impact_score * 0.15) +
            (sla_factor * 0.15)
        )

        # Tier classification (High risk issues are guaranteed CRITICAL tier)
        if high_risk_flags or composite >= 3.0:
            tier = "CRITICAL"
        elif composite >= 2.3:
            tier = "HIGH"
        elif composite >= 1.6:
            tier = "MEDIUM"
        else:
            tier = "LOW"

        return {
            "tier": tier,
            "composite_score": round(composite, 2),
            "factors": {
                "severity_score": sev_score,
                "sentiment_score": sent_score,
                "waiting_time_score": wait_score,
                "customer_impact_score": impact_score,
                "sla_escalation_factor": sla_factor
            }
        }

priority_calculator = PriorityCalculator()
