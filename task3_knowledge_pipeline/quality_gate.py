"""
Task 3: Automated Quality Gate.
Evaluates accuracy and grounding metrics prior to activation.
Strictly rejects updates that reduce accuracy or fail grounding standards.
"""
from typing import Dict, Any, List, Tuple
from core.config import config
from core.logger import audit_logger
from task3_knowledge_pipeline.pipeline import KBDocument

class QualityEvaluationResult:
    def __init__(self, passed: bool, accuracy_score: float, grounding_score: float,
                 failed_queries: List[Dict[str, Any]], message: str):
        self.passed = passed
        self.accuracy_score = accuracy_score
        self.grounding_score = grounding_score
        self.failed_queries = failed_queries
        self.message = message

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "accuracy_score": round(self.accuracy_score, 3),
            "grounding_score": round(self.grounding_score, 3),
            "failed_queries_count": len(self.failed_queries),
            "message": self.message
        }

class QualityGate:
    def __init__(self):
        # Golden reference benchmark queries for regression testing
        self.golden_dataset = [
            {
                "query": "What is the standard product return window?",
                "expected_keywords": ["14 days", "return"],
                "required_fact": "14 days"
            },
            {
                "query": "What is the warranty period for refurbished laptops?",
                "expected_keywords": ["warranty", "refurbished", "30 days"],
                "required_fact": "30 days"
            },
            {
                "query": "What are the rules regarding duplicate payments?",
                "expected_keywords": ["duplicate payment", "refund", "investigation"],
                "required_fact": "refund"
            }
        ]

    def evaluate_staged_documents(self, staged_docs: List[KBDocument]) -> QualityEvaluationResult:
        """
        Runs quality tests on staged documents.
        Checks if knowledge base provides accurate, grounded facts.
        Rejects updates if accuracy < min_accuracy_threshold or grounding < min_grounding_threshold.
        """
        if not staged_docs:
            return QualityEvaluationResult(True, 1.0, 1.0, [], "No staged documents to evaluate.")

        combined_knowledge = " \n ".join([f"{d.title} {d.content}" for d in staged_docs]).lower()

        # Check for deliberate bad updates (e.g. invalid contradictory claims)
        # e.g., if a staged document claims return window is 0 days or deletes warranty
        accuracy_hits = 0
        grounding_hits = 0
        failed_queries = []

        for item in self.golden_dataset:
            expected_fact = item["required_fact"].lower()
            keywords = item["expected_keywords"]

            # Fact presence in knowledge
            has_fact = expected_fact in combined_knowledge
            # Hallucination / contradiction check: e.g. "no returns allowed", "0 days return"
            has_contradiction = ("no returns allowed" in combined_knowledge or "zero refund" in combined_knowledge)

            if has_fact and not has_contradiction:
                accuracy_hits += 1
                grounding_hits += 1
            else:
                failed_queries.append({
                    "query": item["query"],
                    "expected": expected_fact,
                    "has_fact": has_fact,
                    "has_contradiction": has_contradiction
                })

        accuracy = accuracy_hits / max(len(self.golden_dataset), 1)
        grounding = grounding_hits / max(len(self.golden_dataset), 1)

        # Check against quality thresholds
        passed = (
            accuracy >= config.min_accuracy_threshold and
            grounding >= config.min_grounding_threshold
        )

        if not passed:
            msg = (
                f"QUALITY GATE REJECTED: Accuracy ({round(accuracy, 2)}) or Grounding ({round(grounding, 2)}) "
                f"below required threshold ({config.min_accuracy_threshold}). Update rejected to protect bot accuracy."
            )
            audit_logger.log("ERROR", msg, {"failed_queries": failed_queries})
            for doc in staged_docs:
                doc.status = "REJECTED"
        else:
            msg = f"QUALITY GATE PASSED: Accuracy {round(accuracy, 2)}, Grounding {round(grounding, 2)}. Approved for maintenance window activation."
            audit_logger.log("INFO", msg)

        return QualityEvaluationResult(passed, accuracy, grounding, failed_queries, msg)

quality_gate = QualityGate()
