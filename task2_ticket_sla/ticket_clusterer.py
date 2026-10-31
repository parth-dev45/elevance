"""
Task 2: Duplicate Ticket Detection, Issue Clustering, and Masked Handoff Summaries.
Detects redundant requests, groups related incidents, and separates unrelated issues.
"""
from typing import List, Dict, Any, Tuple, Optional
import re
from core.security import security_service
from task2_ticket_sla.sla_manager import Ticket

class TicketClusterer:
    def __init__(self):
        pass

    def _tokenize(self, text: str) -> set:
        """Helper to extract clean lowercase word tokens."""
        words = re.findall(r'\b[a-z]{3,}\b', (text or "").lower())
        # Filter out common stop words
        stop_words = {"the", "and", "for", "with", "this", "that", "have", "from", "your", "order", "item", "please", "help"}
        return set(w for w in words if w not in stop_words)

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculates Jaccard token similarity between two issue descriptions."""
        tokens1 = self._tokenize(text1)
        tokens2 = self._tokenize(text2)
        if not tokens1 or not tokens2:
            return 0.0
        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)
        return len(intersection) / len(union)

    def detect_duplicate(self, candidate_issue: str, customer: str,
                         order_id: Optional[str],
                         active_tickets: List[Ticket]) -> Tuple[bool, Optional[str]]:
        """
        Checks if candidate request is a duplicate of an existing active ticket.
        Returns: (is_duplicate: bool, original_ticket_id: Optional[str])
        """
        for t in active_tickets:
            if t.status in ["RESOLVED"]:
                continue

            # Check match on order ID
            if order_id and t.order_id and order_id.strip().upper() == t.order_id.strip().upper():
                sim = self.calculate_similarity(candidate_issue, t.issue)
                # If same customer or any topic overlap on same order -> duplicate request
                if sim >= 0.15 or (customer and t.customer and customer.strip().lower() == t.customer.strip().lower()):
                    return True, t.ticket_id

            # Check same customer + very high semantic overlap
            if customer and t.customer and customer.strip().lower() == t.customer.strip().lower():
                sim = self.calculate_similarity(candidate_issue, t.issue)
                if sim >= 0.65:
                    return True, t.ticket_id

        return False, None

    def group_and_separate_issues(self, tickets: List[Ticket]) -> Dict[str, List[Ticket]]:
        """
        Groups related issues together based on common topic clusters,
        while maintaining distinct separation for unrelated issues.
        """
        clusters: Dict[str, List[Ticket]] = {}
        for ticket in tickets:
            assigned = False
            # Check against existing clusters
            for cluster_name, cluster_tickets in clusters.items():
                rep = cluster_tickets[0]
                # If either order ID matches or issue similarity is high, add to cluster
                same_order = (ticket.order_id and rep.order_id and ticket.order_id.strip().upper() == rep.order_id.strip().upper())
                sim = self.calculate_similarity(ticket.issue, rep.issue)
                if same_order or sim >= 0.50:
                    clusters[cluster_name].append(ticket)
                    assigned = True
                    break

            if not assigned:
                # Create a new isolated cluster for unrelated issue
                topic_snippet = " ".join(list(self._tokenize(ticket.issue))[:3]).title() or "General"
                cluster_key = f"Cluster_{topic_snippet}_{ticket.ticket_id}"
                clusters[cluster_key] = [ticket]

        return clusters

    def generate_masked_handoff_summary(self, ticket: Ticket, context: Optional[str] = None) -> str:
        """
        Generates a comprehensive, PII-masked handoff summary for human support agents.
        """
        raw_summary = (
            f"Ticket ID: {ticket.ticket_id}\n"
            f"Customer: {ticket.customer}\n"
            f"Order ID: {ticket.order_id or 'N/A'}\n"
            f"Product: {ticket.product or 'N/A'}\n"
            f"Priority: {ticket.priority_tier}\n"
            f"Target Queue: {ticket.target_queue}\n"
            f"Assigned Agent: {ticket.assigned_agent_id or 'Unassigned'}\n"
            f"Contact: {ticket.contact_details or 'N/A'}\n"
            f"Evidence: {ticket.evidence or 'None'}\n"
            f"Issue Details: {ticket.issue}\n"
        )
        if context:
            raw_summary += f"Conversation Context:\n{context}\n"

        masked_text = security_service.mask_pii(raw_summary)
        handoff_document = (
            "====================================================\n"
            "            OFFICIAL AGENT HANDOFF SUMMARY          \n"
            "   (Sensitive customer data redacted for privacy)   \n"
            "====================================================\n"
            f"{masked_text}"
            "===================================================="
        )
        ticket.masked_summary = handoff_document
        return handoff_document

ticket_clusterer = TicketClusterer()
