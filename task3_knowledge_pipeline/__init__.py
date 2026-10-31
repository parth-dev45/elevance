"""
Task 3: Knowledge Base CI/CD Pipeline & Monitoring package.
"""
from task3_knowledge_pipeline.pipeline import kb_pipeline, KBPipeline, KBDocument, IngestionResult
from task3_knowledge_pipeline.quality_gate import quality_gate, QualityGate, QualityEvaluationResult
from task3_knowledge_pipeline.scheduler import kb_scheduler, KBScheduler, ScheduledUpdateJob
from task3_knowledge_pipeline.version_manager import kb_version_manager, KBVersionManager, VersionSnapshot
from task3_knowledge_pipeline.observability import observability_service, ObservabilityService

__all__ = [
    "kb_pipeline",
    "KBPipeline",
    "KBDocument",
    "IngestionResult",
    "quality_gate",
    "QualityGate",
    "QualityEvaluationResult",
    "kb_scheduler",
    "KBScheduler",
    "ScheduledUpdateJob",
    "kb_version_manager",
    "KBVersionManager",
    "VersionSnapshot",
    "observability_service",
    "ObservabilityService",
]
