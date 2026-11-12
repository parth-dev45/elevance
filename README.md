# Elevance Enterprise AI Customer Support & Knowledge Intelligence Platform

An enterprise-grade, autonomous customer support AI platform engineered for **ElevanceSkills Technology Private Limited**, featuring multilingual sentiment escalation, business-calendar SLA management, CI/CD knowledge base updates with canary rollback, temporal RAG with access control, multimodal OCR invoice cross-validation, and multilingual code-switching with session lifecycle management.

---

## 🌟 Key Features & Task Architecture

| Task | Module | Key Capabilities |
|---|---|---|
| **Task 1** | `task1_sentiment_escalation/` | Multilingual sentiment analysis (`positive`, `neutral`, `negative`, `frustrated`, `urgent`, `sarcastic`), incongruity-based sarcasm detection, tone adaptation preserving business policies, calm high-risk detection (legal threats, compromise, duplicate charges), after-hours on-call routing, >15m unresolved negative conversation escalation. |
| **Task 2** | `task2_ticket_sla/` | Structured ticket generation, entity extraction with missing mandatory field prompts, multi-factor priority calculator, skill & capacity-based agent routing, unavailable team fallback, weekend/holiday-excluding SLA engine, 75% warning and 100% breach escalation, runtime SLA updates, duplicate clustering, masked handoff summaries. |
| **Task 3** | `task3_knowledge_pipeline/` | Content-hash delta ingestion, duplicate doc detection, quarantine vault, pre-activation accuracy/grounding quality gate (min 85%), maintenance window gatekeeper (01:00-05:00), exponential retry sequence (15m, 30m, 60m), 5-minute automated canary rollback, observability metrics. |
| **Task 4** | `task4_rag_assistant/` | Temporal vector retrieval with metadata (version, product, region, access level, effective/expiry dates), RBAC permission enforcement, conflict resolution picking latest applicable version, active vs historical date policy filtering, prompt injection defense, exact source citations, refusal on missing evidence. |
| **Task 5** | `task5_multimodal_ocr/` | Multimodal OCR engine for images and PDFs (order IDs, dates, amounts, products, error codes), blur/low-contrast image detection, claim vs invoice cross-validation, unsafe executable & trojan payload rejection, >30s background async queue offloading, automated file retention lifecycle purge. |
| **Task 6** | `task6_multilingual_context/` | Multilingual support (English, Hindi, Spanish, French, German, Hinglish), mid-conversation code-switching, Hinglish transliteration normalizer, typo corrector, entity preservation (names, order IDs, dates, SKUs), user correction handling, 10+ turn context memory, 30m inactivity expiry, 24h conversation summary restoration. |

---

## 🚀 Quickstart Guide

### 1. Environment Setup
```bash
# Activate existing virtual environment
source .venv/bin/activate
```

### 2. Run Complete Test Suite
Run the full test suite of **41 automated tests** covering all 6 assignment tasks and integration flows:
```bash
source .venv/bin/activate && pytest tests/ -v
```

### 3. Launch Web Dashboard & Simulator
Start the FastAPI server:
```bash
source .venv/bin/activate && uvicorn web.app:app --host 127.0.0.1 --port 8000
```
Open your browser at **[http://127.0.0.1:8000](http://127.0.0.1:8000)** to interact with:
- **💬 Live Chat & Sentiment:** Interactive chat with sentiment badge, tone preview, and quick test scenarios (Sarcastic Complaint, Calm Legal Threat, Duplicate Payment, Hinglish, Prompt Injection).
- **🎫 Tickets & Dynamic SLA:** Live ticket triage queue with SLA progress bars, priority badges, masked handoff summaries, and runtime SLA modification sliders.
- **📚 KB Pipeline & CI/CD:** Staged document manager, pre-activation quality gate tester, maintenance window publisher, and 5-min canary health monitor.
- **🔍 Multimodal OCR Lab:** Upload invoices or screenshots, test simulated processing delays (>30s async queue), and inspect claim vs evidence cross-validation.
- **⏱️ Virtual Time Machine:** Advance simulated time (+15m, +4h, jump to after-hours, advance +25h) to test SLA triggers and session lifecycles.

---

## 📂 Project Directory Structure

```
Elevance-project/
├── core/
│   ├── config.py              # Dynamic system configuration & SLA thresholds
│   ├── time_engine.py         # Simulated virtual clock & business calendar
│   ├── security.py            # PII masking, RBAC, and prompt injection sanitizer
│   └── logger.py              # Structured telemetry & escalation audit trail
├── task1_sentiment_escalation/
│   ├── sentiment_analyzer.py  # Multilingual sentiment & sarcasm engine
│   ├── tone_adapter.py        # Tone modulation preserving business policies
│   └── escalation_engine.py   # High-risk, duration, and after-hours escalation
├── task2_ticket_sla/
│   ├── entity_extractor.py    # Entity parsing & clarification prompt generator
│   ├── priority_calculator.py # 5-factor weighted priority scoring engine
│   ├── routing_engine.py      # Skill, capacity, and unavailable team routing
│   ├── sla_manager.py         # Weekend/holiday SLA engine with 75% warning & breach
│   └── ticket_clusterer.py    # Deduplication, grouping, and masked handoffs
├── task3_knowledge_pipeline/
│   ├── pipeline.py            # Delta ingestion, content hashing, quarantine vault
│   ├── quality_gate.py        # Pre-activation regression accuracy & grounding tests
│   ├── scheduler.py           # Maintenance window gate & 15/30/60m retry sequence
│   ├── version_manager.py     # Snapshot versioning & 5-min canary rollback
│   └── observability.py       # Metrics aggregator & telemetry service
├── task4_rag_assistant/
│   ├── vector_store.py        # Metadata document store & TF-IDF vector index
│   ├── temporal_retriever.py  # Temporal policy retriever & conflict resolver
│   ├── guardrails.py          # Grounding check, prompt defense, citations
│   └── assistant.py           # Grounded RAG conversational assistant
├── task5_multimodal_ocr/
│   ├── ocr_engine.py          # PDF/Image OCR and blur detection engine
│   ├── cross_validator.py     # Claim vs invoice discrepancy cross-checker
│   ├── document_sanitizer.py  # File safety and embedded injection defense
│   ├── async_queue.py         # >30s background request queue manager
│   └── file_retention.py      # Automated retention lifecycle cleanup
├── task6_multilingual_context/
│   ├── language_manager.py    # Multilingual & code-switching detector
│   ├── transliteration_normalizer.py # Hinglish normalizer & typo corrector
│   ├── entity_preserver.py    # Verbatim entity token protector
│   ├── session_manager.py     # Multi-tenant isolation, 30m expiry, 24h summary
│   └── orchestrator.py        # End-to-end chatbot conversation orchestrator
├── web/
│   ├── app.py                 # FastAPI backend server
│   └── static/
│       ├── index.html         # Premium glassmorphic web dashboard
│       ├── css/style.css      # Dark-mode design system
│       └── js/app.js          # Interactive dashboard logic
├── tests/                     # 41 passing automated tests across all tasks
├── docs/
│   └── INTERNSHIP_REPORT.md   # Official 9-section formal internship report
├── pytest.ini                 # Pytest configuration
└── README.md
```

---

## 📋 Formal Internship Deliverables
- **Official Internship Report (PDF & Markdown)**:
  - 📄 **[`docs/INTERNSHIP_REPORT.pdf`](file:///Users/parthbiradar/ACE/Elevance-project/docs/INTERNSHIP_REPORT.pdf)** (Print-ready formatted A4 PDF)
  - 📝 **[`docs/INTERNSHIP_REPORT.md`](file:///Users/parthbiradar/ACE/Elevance-project/docs/INTERNSHIP_REPORT.md)** (Full 9-section Markdown report)
  - 🌐 **[`docs/INTERNSHIP_REPORT.html`](file:///Users/parthbiradar/ACE/Elevance-project/docs/INTERNSHIP_REPORT.html)** (Interactive HTML report)
- **Live Website Walkthrough Video**:
  - 🎥 **[`demo_walkthrough.mp4`](file:///Users/parthbiradar/ACE/Elevance-project/demo_walkthrough.mp4)** (Full HD 1080p video recording of the live running web application with spoken voiceover)
- **Production Datasets & Evaluation Benchmarks**:
  - 📦 **[`datasets_elevance_support_ai.zip`](file:///Users/parthbiradar/ACE/Elevance-project/datasets_elevance_support_ai.zip)** (Complete zip archive of all datasets across tasks 1 to 6)
  - 🗂️ **[`datasets/`](file:///Users/parthbiradar/ACE/Elevance-project/datasets/)** (Directory containing JSON corpora, policy manifests, holiday calendars, and sample OCR documents)

