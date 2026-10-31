# ELEVANCESKILLS TECHNOLOGY PRIVATE LIMITED
## OFFICIAL INTERNSHIP COMPLETION REPORT

---

**Candidate Name:** PARTH BIRADAR  
**Host Organization:** ElevanceSkills Technology Private Limited  
**Department / Track:** Advanced Agentic Artificial Intelligence & Enterprise Engineering  
**Project Title:** Autonomous Multilingual Enterprise Customer Support & Knowledge Intelligence Platform  
**Date of Submission:** October 31, 2026  
**Review Status:** Final Submission for Evaluation and Stipend Award  

---

## 1. Introduction

This formal internship report documents the architecture, implementation, validation, and outcomes of the **Autonomous Multilingual Enterprise Customer Support & Knowledge Intelligence Platform**, developed during the engineering internship program at ElevanceSkills Technology Private Limited.

Modern customer service operations require systems that transcend rigid, keyword-based chatbots. Global enterprises handle high volumes of inquiries across multiple spoken and transliterated languages, demanding nuanced sentiment identification (distinguishing genuine praise from sharp sarcasm), dynamic regulatory and business-hour service-level agreements (SLAs), strict compliance and data protection (PII masking and prompt injection defense), automated document updates with rollback safeguards, grounded question-answering with verifiable citations, and multimodal invoice/evidence cross-verification.

To address these requirements, this project delivers a unified, production-ready enterprise customer support system encompassing all six assigned tasks within an integrated architectural framework. The system is backed by a robust FastAPI REST infrastructure, a glassmorphic real-time observability dashboard, a simulated time-travel engine for evaluation, and an automated test suite comprising 41 passing unit and integration tests.

---

## 2. Background

Customer support centers represent critical operational touchpoints where customer satisfaction directly influences brand retention and lifetime value. However, legacy conversational systems suffer from pervasive failure modes:
1. **Tone Deafness & Misclassification:** Traditional sentiment models fail to detect nuanced emotions such as frustration, urgency, and sarcasm—frequently misclassifying sarcastic complaints with outwardly positive vocabulary (e.g., *"Oh fantastic, my order hasn't arrived in 3 weeks, stellar service guys!"*) as positive feedback.
2. **Static & Fragile Routing:** Escalations often rely on simplistic trigger rules, missing calm high-risk threats (e.g., politely phrased legal or regulatory notices) and failing to adapt to off-hours availability or agent skill sets.
3. **SLA Calculation Blind Spots:** Standard ticketing systems measure elapsed wall-clock time rather than official business hours, incorrectly counting weekends and statutory holidays, which leads to artificial breaches and misallocated human resources.
4. **Knowledge Drift & Hallucination:** Chatbots frequently recite expired policies, confuse regional guidelines, or fabricate terms when authoritative documentation is missing.
5. **Multimodal Discrepancies:** Support agents spend extensive manual effort cross-referencing customer text claims against attached invoices, screenshots, and receipts.
6. **Code-Switching & Session Loss:** Customers in multilingual regions (such as India, Europe, and Latin America) frequently mix languages or use phonetic Latin-script transliterations (e.g., Hinglish), while arbitrary session timeouts wipe valuable context.

This project was engineered to solve these operational dilemmas through an enterprise-grade, modular AI architecture.

---

## 3. Learning Objectives

The internship pursued several technical and professional development milestones:
- **Architectural Design:** Engineer a modular, maintainable, production-ready backend uniting six distinct enterprise AI capabilities into a cohesive dialogue and ticketing engine.
- **Natural Language Understanding & Emotion Detection:** Implement multilingual sentiment analysis capable of detecting positive, neutral, negative, frustrated, urgent, and sarcastic intents, including incongruence heuristics for sarcasm and keyword-independent high-risk detection.
- **Dynamic SLA & Routing Mathematics:** Formulate business-calendar time engines that skip non-working hours, weekends, and holidays, triggering proactive warnings at 75% consumption and automated escalations at 100% breach.
- **Continuous Integration for Knowledge Bases:** Build safe automated ingestion pipelines with content hashing, delta processing, quarantine vaults, pre-activation quality gates, maintenance window locks, and canary rollback mechanisms.
- **Temporal Retrieval-Augmented Generation (RAG):** Design metadata-driven policy retrieval that filters by version, product, region, access level, and effective dates, strictly resolving conflicts and guaranteeing verifiable source citations.
- **Multimodal Document Processing:** Develop OCR extraction pipelines for invoices and screenshots that cross-validate evidence against user claims, reject blurred files, offload long-running tasks (>30s) to background queues, and purge expired uploads.
- **Context & Session Management:** Build isolated multi-tenant session state machines with 10+ turn history retention, 30-minute inactivity timeouts, and 24-hour summary restoration for returning customers.

---

## 4. Activities and Tasks

The project successfully implemented all six core assignments into an integrated framework:

### Task 1: Multilingual Sentiment Analysis & Escalation Engine
- **Multilingual Lexical & Pattern Recognition:** Analyzes incoming customer messages and conversation history to classify sentiment across six distinct states: `positive`, `neutral`, `negative`, `frustrated`, `urgent`, and `sarcastic`.
- **Sarcasm Detection Engine:** Implements dual-signal incongruence detection that identifies positive sentiment words paired with explicit complaint indicators (delays, broken items, missing packages, excessive punctuation), ensuring sarcastic messages are not mislabeled as positive.
- **Tone Adapter:** Dynamically adapts response tone (empathetic, reassuring, apologetic, direct, or professional) based on detected emotion while preserving all business policy terms, numerical refund windows, and warranty figures unchanged.
- **Calm High-Risk Detection:** Independently detects legal threats, account compromise, and duplicate payment issues regardless of polite or calm customer phrasing, triggering immediate escalation.
- **Business Hours & Time Engine:** Evaluates current operational hours (09:00 - 18:00 Mon-Fri). Urgent complaints received outside business hours enter a 24/7 on-call emergency queue, while normal complaints are scheduled for the next working day at 09:00 AM.
- **Duration-Based Escalation:** Unresolved negative conversations exceeding 15 minutes trigger automated escalation, recording the trigger reason, activated condition, and an anonymized conversation summary.

### Task 2: Structured Ticket Generation, Dynamic Routing & SLA Management
- **Entity Extractor:** Automatically extracts customer name, order ID, product, issue details, evidence, and contact details (email/phone) from conversation turns. Identifies missing mandatory fields and generates targeted clarification prompts.
- **Multi-Factor Priority Scoring:** Computes ticket priority (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`) using a weighted composite formula incorporating severity (35%), sentiment/urgency (20%), waiting time (15%), customer tier (15%), and escalation status (15%). High-risk issues automatically receive `CRITICAL` priority.
- **Skill & Workload-Aware Routing:** Routes tickets based on required skill (billing, technical, returns, general), active agent online status, current ticket load vs. maximum capacity, and business hours.
- **Unavailable Team Fallback:** If all agents with a matching skill are offline or at capacity, the system routes the ticket to a general overflow pool with an alert flag, preventing dropped requests.
- **Weekend & Holiday-Excluding SLA Engine:** Calculates deadlines strictly within configured business hours, skipping weekends and configured public holidays. Emits automated warnings at 75% time consumption and executes automated breach escalation at 100%.
- **Runtime SLA Configuration:** Supports dynamic runtime changes to SLA policy hours, automatically re-evaluating deadlines and statuses for all open tickets.
- **Ticket Deduplication & Clustering:** Detects duplicate requests for the same order or issue, groups related incidents into topical clusters, isolates unrelated issues, and generates PII-masked handoff summaries.

### Task 3: Knowledge Base Pipeline & CI/CD with Monitoring
- **Delta Ingestion & Content Hashing:** Computes SHA-256 content hashes over documents and metadata. Only new or modified documents are staged; duplicate documents are flagged and skipped.
- **Quarantine Vault:** Automatically isolates invalid files (missing titles, empty content) and prompt-injection payloads into `data/quarantine/`.
- **Pre-Activation Quality Gate:** Runs an automated golden regression benchmark evaluating factual accuracy and grounding. Rejects updates that degrade accuracy or grounding below the 85% threshold.
- **Scheduler & Retry Engine:** Updates can be scheduled for future execution. Failed jobs automatically retry following an exponential sequence of 15, 30, and 60 minutes.
- **Maintenance Window Gatekeeper:** Activates approved updates strictly during the configured maintenance window (01:00 - 05:00), holding daytime activations until the window opens.
- **5-Minute Canary Health Check Rollback:** Following activation, monitors system health. If an error spike (>10%) or simulated outage occurs within 5 minutes, the system automatically executes an emergency rollback to the previous stable snapshot.
- **Observability & RBAC:** Enforces administrator-only access for knowledge management, neutralizes embedded prompt injections, applies PII masking, and tracks latency, failure rates, and escalation counts.

### Task 4: Temporal RAG Knowledge Assistant with Access Control & Guardrails
- **Metadata Document Store:** Stores document version, product, region, access level (`public`, `internal`, `confidential`), effective date, and expiry date.
- **RBAC Policy Filtering:** Enforces strict role boundaries; customers cannot retrieve internal or confidential documents, preventing data leakage.
- **Temporal Policy Retrieval:**
  - *Current Inquiries:* Evaluates policies active today, strictly ignoring future-dated policies (`effective_date > today`) and expired policies (`expiry_date < today`).
  - *Historical Inquiries:* Extracts customer-specified dates from natural language (e.g., *"back on 2022-08-10"*) and retrieves the policy active on that exact historical date.
- **Conflict Resolution:** When multiple applicable versions exist for a product or policy, the retriever sorts by effective date and version descending, selecting the latest applicable policy.
- **Document Prompt-Injection Sanitization:** Scans and strips embedded malicious directives (e.g., trojan instructions embedded in policy texts) before synthesis.
- **Mandatory Source Citations:** Every factual response includes verified policy citations: `[Source: {title} (Doc ID: {id}, Version: {v}, Effective: {date})]`.
- **Refusal on Missing Evidence:** When authoritative evidence is absent or ambiguous, the bot refuses to speculate and requests clarification.

### Task 5: Multimodal OCR & Document Verification Pipeline
- **Document & Image OCR:** Analyzes PNG, JPG, WEBP, and PDF files, extracting order IDs, dates, currency amounts, product descriptions, and error codes.
- **Blur & Low-Quality Detection:** Evaluates image resolution, contrast, and Laplacian edge variance. Unreadable or blurry files are rejected with a request for a clearer image or PDF.
- **Claim vs. Evidence Cross-Validation:** Compares OCR data against customer message claims, detecting discrepancies in amounts, order IDs, or products and generating polite clarification prompts.
- **No Hallucinated Missing Values:** Missing fields remain `None` and are never fabricated.
- **File Security Sanitization:** Blocks dangerous executable file extensions (`.exe`, `.sh`, `.bat`, `.py`) and inspects file content and OCR text for hidden prompt injections.
- **Async Background Queue:** Processing exceeding 30 seconds is offloaded to a background queue (`ASYNC-OCR-XXXX`), immediately providing the customer with a tracking job ID.
- **File Retention Lifecycle:** Uploaded files are registered with a configurable retention period (default 24 hours). Expired files are permanently purged from disk.

### Task 6: Multilingual Session Management, Transliteration & Context Engine
- **Multilingual Support:** Supports English, Hindi, Spanish, French, German, and Hinglish.
- **Dynamic Code-Switching:** Detects language switching within the same conversation or mixed-language messages, dynamically responding in the appropriate language.
- **Transliteration & Typo Correction:** Normalizes Latin-script phonetic Hindi (Hinglish) into standardized semantic representations and fixes common customer service typos.
- **Entity Preservation:** Verbatim preservation of customer names, order IDs, dates, and SKUs across language transformations using replacement tokens.
- **User Correction Handling:** Identifies when customers correct themselves mid-turn (e.g., *"My order is ORD-1111. Actually wait, it's ORD-9999"*), updating internal state to the corrected entity.
- **Session Lifecycle & Continuity:**
  - Isolates simultaneous customer sessions with zero state leakage.
  - Maintains conversation history across 10+ turns.
  - Automatically expires sessions after 30 minutes of inactivity.
  - If a customer returns within 24 hours of session close, restores their previous conversation summary.
  - If returning after 24 hours, initiates a fresh session.

---

## 5. Skills and Competencies

Through the execution of this project, proficiency was demonstrated in the following competencies:
- **Backend Architecture & Web APIs:** FastAPI, Uvicorn, RESTful endpoint design, Pydantic data modeling, asynchronous request processing.
- **Natural Language Processing & Information Retrieval:** TF-IDF vectorization, cosine similarity metrics, regex tokenization, sentiment heuristics, language detection.
- **Cybersecurity & Compliance:** Role-Based Access Control (RBAC), PII redaction algorithms, adversarial prompt-injection detection, file sanitization.
- **Time Engines & Business Calendars:** Simulated virtual clocks, business-day stepping algorithms, holiday/weekend exclusion logic.
- **Computer Vision & OCR:** Pillow image processing, edge detection, variance-based blur scoring, PDF text extraction.
- **Testing & Quality Assurance:** Comprehensive test-driven development with `pytest`, covering unit, integration, and failure-mode test suites.
- **Frontend & UX Engineering:** Modern dark-mode web design, glassmorphism, responsive CSS grid layouts, real-time metrics dashboards.

---

## 6. Feedback and Evidence

The platform's reliability and compliance were verified through exhaustive testing:

### Test Suite Execution
A comprehensive test suite of **41 automated tests** was executed via `pytest`, achieving **100% pass rate** across all assignment requirements:
- `tests/test_task1_sentiment.py`: Sarcasm detection, calm high-risk threats, duplicate payment triggers, tone adaptation, repeated negative escalation, 15-minute unresolved negative timer, after-hours on-call routing. (7/7 passed)
- `tests/test_task2_tickets.py`: Entity extraction, mandatory field clarification prompts, priority calculation, skill and workload routing, unavailable team fallbacks, weekend/holiday SLA calculations (75% warning and 100% breach), runtime SLA policy modification, duplicate ticket clustering, masked handoff summaries. (7/7 passed)
- `tests/test_task3_pipeline.py`: RBAC access control, content-hash delta ingestion, duplicate document detection, quarantine isolation, pre-activation quality gate rejection, maintenance window scheduling, 15/30/60-minute retry sequences, 5-minute automated canary rollback. (6/6 passed)
- `tests/test_task4_rag.py`: Current vs. future vs. expired policy filtering, historical date retrieval, conflicting policy resolution, RBAC document permissions, embedded prompt-injection neutralization, missing evidence refusal. (6/6 passed)
- `tests/test_task5_multimodal.py`: OCR field parsing, invoice discrepancy cross-validation, blurry image rejection, unsafe file rejection, hidden OCR injection detection, >30s async queue offloading, file retention expiry purge. (6/6 passed)
- `tests/test_task6_multilingual.py`: Multilingual detection, code-switching, Hinglish transliteration, spelling correction, entity preservation, user correction handling, session isolation, 10+ turn context memory, 30-min inactivity expiry, 24-hr summary restoration. (7/7 passed)
- `tests/test_integration.py`: Multi-turn end-to-end customer journey testing high-risk escalation, ticket generation, deduplication, and grounded RAG citations. (2/2 passed)

### Browser Subagent Visual & Functional Verification
The interactive web dashboard (`http://127.0.0.1:8000`) was verified using an autonomous browser subagent:
- Verified responsive layout, topbar branding, real-time clock, and business-hours status indicator.
- Tested live conversational chat using quick scenario presets (Sarcastic Complaint, Calm Legal Threat, Hinglish, Prompt Injection).
- Verified ticket triage board displaying active tickets, priority badges, SLA progress bars, and masked handoff summaries.
- Executed automated pre-activation quality checks on staged knowledge base documents.
- Tested virtual clock adjustments and verified telemetry metric displays.

The recorded session artifact is available at: `dashboard_interaction_1793422083743.webp`.

---

## 7. Challenges and Solutions

| Challenge Encountered | Root Cause | Engineering Solution Implemented |
|---|---|---|
| **Sarcastic Messages Misclassified** | Traditional positive word counts misclassify sarcastic phrases like *"Oh fantastic, my order hasn't arrived"* as positive. | Implemented an incongruence detection algorithm that cross-checks high positive valence against explicit complaint markers (delays, broken items, missing packages, exclamation marks), classifying them accurately as sarcastic/frustrated. |
| **Calm High-Risk Complaints Evading Triggers** | Customers using calm, polite phrasing (e.g., *"Good morning, I have informed my attorney"*) produce low negative sentiment scores. | Decoupled high-risk issue detection (legal threats, account compromise, duplicate charges) from emotional valence, ensuring high-risk flags trigger immediate escalation regardless of calm phrasing. |
| **Accurate Business Hours & SLA Calculations** | Wall-clock calculations incorrectly count weekends, holidays, and nights, causing false SLA breaches. | Built a custom `TimeEngine` that steps through time strictly accounting for working hours (09:00 - 18:00 Mon-Fri) while skipping configured public holidays and weekends. |
| **Conflicting & Future-Dated Knowledge Policies** | Knowledge bases often contain overlapping versions or future policies that bots inadvertently recite. | Built a temporal retriever that filters documents against a target date (current date or customer-specified historical date) and resolves conflicts by selecting the latest effective applicable version. |
| **OCR Field False Positives** | Contact phone numbers (e.g. `415-555-2671`) were inadvertently matched as order IDs, and compound words like `headphones` were matched as `phone`. | Refined regex patterns with word boundaries, required alphanumeric prefixes for order IDs, and sorted product keywords by length descending to match compound terms accurately. |
| **Session Inactivity vs. Context Restoration** | Inactivity timeouts must close sessions to free resources without permanently losing context if the customer returns promptly. | Created a dual-window session lifecycle: sessions close after 30 minutes of inactivity, but an anonymized conversation summary is preserved for 24 hours, enabling instant context restoration if the customer returns within that window. |

---

## 8. Outcomes and Impact

1. **Autonomous Issue Resolution & Safe Escalation:** Routine inquiries (returns, warranty, shipping) are resolved instantly via grounded RAG, while high-risk or complex issues are routed with structured tickets, priority scoring, and PII-masked handoffs.
2. **Elimination of SLA False Alarms:** Business-calendar SLA calculation prevents false breach alerts over weekends and holidays, while the 75% warning threshold enables proactive supervisor intervention before breaches occur.
3. **Zero-Downtime Knowledge Deployments:** Pre-activation quality gates prevent inaccurate policy updates, maintenance window restrictions avoid user disruptions, and the 5-minute automated canary rollback protects against regressions.
4. **Data Protection & Compliance:** Comprehensive PII masking across all logs, ticket summaries, and handoff notes shields sensitive customer information, and prompt-injection defenses neutralize adversarial inputs in both chat and uploaded documents.
5. **Enhanced Global Customer Accessibility:** Support for multiple languages, code-switching, and Hinglish transliterations ensures inclusive communication, while entity preservation maintains critical order and SKU identifiers across all interactions.

---

## 9. Conclusion

The internship project successfully designed, implemented, and validated the **Autonomous Multilingual Enterprise Customer Support & Knowledge Intelligence Platform**, fulfilling all requirements specified across the six assigned tasks.

The delivered codebase demonstrates clean modular architecture, adherence to security best practices, and thorough automated test coverage (41/41 passing tests). The accompanying web application provides an intuitive interface for live chat, ticket management, knowledge base deployments, multimodal document analysis, and time-travel evaluation.

This experience provided deep practical exposure to advanced AI agent design, temporal retrieval systems, resilient software architectures, and automated testing in enterprise environments. The completed platform stands ready for production deployment, and all project deliverables and documentation are formally submitted for final evaluation.

---

*Report prepared and submitted by:*  
**PARTH BIRADAR**  
*Intern, ElevanceSkills Technology Private Limited*
