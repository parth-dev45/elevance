"""
FastAPI Enterprise Application Backend for Elevance AI Platform.
Exposes REST endpoints for Chatbot Orchestrator, Tickets & SLA, Knowledge CI/CD,
Multimodal OCR, Time Travel Simulator, and Observability Telemetry.
"""
import os
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from core.time_engine import time_engine
from core.config import config
from core.security import UserRole, security_service
from core.logger import audit_logger
from task1_sentiment_escalation.sentiment_analyzer import sentiment_analyzer
from task2_ticket_sla.sla_manager import sla_manager
from task2_ticket_sla.routing_engine import routing_engine
from task2_ticket_sla.ticket_clusterer import ticket_clusterer
from task3_knowledge_pipeline.pipeline import kb_pipeline, KBDocument
from task3_knowledge_pipeline.quality_gate import quality_gate
from task3_knowledge_pipeline.scheduler import kb_scheduler
from task3_knowledge_pipeline.version_manager import kb_version_manager
from task3_knowledge_pipeline.observability import observability_service
from task4_rag_assistant.assistant import rag_assistant
from task5_multimodal_ocr.ocr_engine import ocr_engine
from task5_multimodal_ocr.cross_validator import cross_validator
from task5_multimodal_ocr.document_sanitizer import document_sanitizer
from task5_multimodal_ocr.async_queue import async_queue_manager
from task5_multimodal_ocr.file_retention import file_retention_manager
from task6_multilingual_context.orchestrator import chatbot_orchestrator
from task6_multilingual_context.session_manager import session_manager

app = FastAPI(title="Elevance Enterprise Customer Support AI Platform", version="1.0.0")

# Request Models
class ChatRequest(BaseModel):
    customer_id: str = "customer_demo"
    message: str
    user_role: str = "customer"
    customer_tier: str = "standard"

class TimeSetRequest(BaseModel):
    timestamp_iso: Optional[str] = None
    advance_minutes: Optional[float] = None
    advance_hours: Optional[float] = None
    advance_days: Optional[float] = None
    reset: bool = False

class SLAUpdateRequest(BaseModel):
    priority_tier: str
    business_hours: float

class KBIngestRequest(BaseModel):
    doc_id: str
    title: str
    content: str
    version: str = "1.0"
    product: str = "general"
    access_level: str = "public"
    effective_date: str = "2024-01-01"
    expiry_date: Optional[str] = None

# --- API ENDPOINTS ---

@app.post("/api/chat")
def handle_chat(req: ChatRequest):
    role = UserRole(req.user_role.lower()) if req.user_role.lower() in [r.value for r in UserRole] else UserRole.CUSTOMER
    resp = chatbot_orchestrator.process_turn(
        customer_id=req.customer_id,
        message=req.message,
        user_role=role,
        customer_tier=req.customer_tier
    )
    return resp.to_dict()

@app.get("/api/tickets")
def get_tickets():
    # Evaluate SLA for all open tickets
    sla_manager.evaluate_all()
    tickets_list = [t.model_dump() for t in sla_manager.tickets.values()]
    # Sort by created_at desc
    tickets_list.sort(key=lambda x: str(x.get("created_at")), reverse=True)
    return {
        "tickets": tickets_list,
        "agents": [a.model_dump() for a in routing_engine.agents.values()],
        "sla_hours_map": config.sla_hours_map
    }

@app.post("/api/sla/update")
def update_sla_policy(req: SLAUpdateRequest):
    sla_manager.update_runtime_sla_policy(req.priority_tier, req.business_hours)
    return {
        "status": "UPDATED",
        "priority_tier": req.priority_tier.upper(),
        "new_business_hours": req.business_hours,
        "current_map": config.sla_hours_map
    }

@app.get("/api/kb/status")
def get_kb_status():
    staged = [d.model_dump() for d in kb_pipeline.staged_store.values()]
    active = [d.model_dump() for d in kb_pipeline.active_store.values()]
    now = time_engine.now()
    return {
        "current_version": kb_version_manager.current_version_id,
        "is_maintenance_window": time_engine.is_within_maintenance_window(now),
        "maintenance_window": f"{config.maintenance_window_start_hour:02d}:00 - {config.maintenance_window_end_hour:02d}:00",
        "staged_count": len(staged),
        "active_count": len(active),
        "staged_documents": staged,
        "active_documents": active,
        "snapshots": list(kb_version_manager.snapshots.keys())
    }

@app.post("/api/kb/ingest")
def ingest_kb_document(req: KBIngestRequest):
    doc_payload = {
        "doc_id": req.doc_id,
        "title": req.title,
        "content": req.content,
        "version": req.version,
        "metadata": {
            "product": req.product,
            "access_level": req.access_level,
            "effective_date": req.effective_date,
            "expiry_date": req.expiry_date
        }
    }
    res = kb_pipeline.ingest_documents([doc_payload], user_role=UserRole.ADMIN)
    return res.model_dump()

@app.post("/api/kb/quality-check")
def run_quality_check():
    staged = list(kb_pipeline.staged_store.values())
    res = quality_gate.evaluate_staged_documents(staged)
    return res.to_dict()

@app.post("/api/kb/publish")
def publish_kb(job_id: Optional[str] = None):
    jid = job_id or f"JOB-PUB-{uuid.uuid4().hex[:6].upper()}"
    staged_ids = list(kb_pipeline.staged_store.keys())
    if not staged_ids:
        return {"status": "NO_STAGED_DOCS", "activated": False, "reason": "No documents staged for activation."}

    job = kb_scheduler.schedule_update(jid, staged_ids, user_role=UserRole.ADMIN)
    exec_res = kb_scheduler.execute_job(jid, user_role=UserRole.ADMIN)
    if exec_res.get("activated"):
        kb_version_manager.create_snapshot(f"v{float(kb_version_manager.current_version_id.replace('v', '')) + 0.1:.1f}")
    return exec_res

@app.post("/api/kb/rollback")
def rollback_kb(target_version: str):
    res = kb_version_manager.rollback_to(target_version, reason="Admin Manual Rollback", user_role=UserRole.ADMIN)
    return res

@app.post("/api/kb/canary-check")
def test_canary_health(simulated_error_rate: float = 0.25):
    res = kb_version_manager.verify_canary_health(simulated_error_rate=simulated_error_rate)
    return res

@app.post("/api/multimodal/analyze")
async def analyze_multimodal(
    file: UploadFile = File(...),
    customer_message: str = Form(""),
    simulated_delay_seconds: float = Form(2.0),
    simulated_ocr_text: Optional[str] = Form(None)
):
    upload_dir = "data/uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, f"{uuid.uuid4().hex[:6]}_{file.filename}")

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # 1. Register for automatic retention cleanup
    file_id = file_retention_manager.register_uploaded_file(file_path)

    # 2. Check if processing exceeds 30s threshold
    queue_check = async_queue_manager.dispatch_or_queue(file_path, customer_message, processing_time_seconds=simulated_delay_seconds)
    if queue_check["is_async"]:
        return queue_check

    # 3. Document Safety & hidden injection sanitization
    is_safe, safety_reason = document_sanitizer.sanitize_file(file_path, raw_extracted_text=simulated_ocr_text)
    if not is_safe:
        return {
            "status": "UNSAFE_FILE_REJECTED",
            "is_safe": False,
            "reason": safety_reason,
            "file_id": file_id
        }

    # 4. OCR Extraction
    ocr_res = ocr_engine.process_file(file_path, simulated_ocr_text=simulated_ocr_text)

    # 5. Cross-Validation against customer message
    cross_val = cross_validator.validate(customer_message, ocr_res)

    return {
        "status": "PROCESSED",
        "file_id": file_id,
        "ocr_extracted": ocr_res.model_dump(),
        "cross_validation": cross_val.to_dict()
    }

@app.get("/api/time")
def get_system_time():
    now = time_engine.now()
    return {
        "current_time_iso": now.isoformat(),
        "display_time": now.strftime("%Y-%m-%d %H:%M:%S (%A)"),
        "is_business_hours": time_engine.is_within_business_hours(now),
        "is_maintenance_window": time_engine.is_within_maintenance_window(now),
        "is_simulated": time_engine._simulated_time is not None
    }

@app.post("/api/time/control")
def control_time(req: TimeSetRequest):
    if req.reset:
        time_engine.reset_to_real_time()
    elif req.timestamp_iso:
        dt = datetime.fromisoformat(req.timestamp_iso)
        time_engine.set_time(dt)
    else:
        time_engine.advance_time(
            minutes=req.advance_minutes or 0,
            hours=req.advance_hours or 0,
            days=req.advance_days or 0
        )
    return get_system_time()

@app.get("/api/observability/metrics")
def get_metrics():
    return observability_service.get_dashboard_metrics()

# Mount Static Files
os.makedirs("web/static/css", exist_ok=True)
os.makedirs("web/static/js", exist_ok=True)
app.mount("/static", StaticFiles(directory="web/static"), name="static")

@app.get("/", response_class=HTMLResponse)
def serve_index():
    with open("web/static/index.html", "r", encoding="utf-8") as f:
        return f.read()
