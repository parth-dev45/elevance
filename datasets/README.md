# 📦 Elevance Enterprise Customer Support AI - Datasets Repository

This directory contains the production datasets, ground-truth evaluation corpora, temporal policy manifests, and multilingual conversational logs utilized across all six core tasks of the Elevance Customer Support AI platform.

---

## 🗂️ Dataset Directory Structure

```
datasets/
├── task1_sentiment/
│   └── multilingual_sentiment_escalations.json   # 7+ language sentiment, sarcasm & calm high-risk corpus
├── task2_tickets_sla/
│   └── structured_tickets_sla_dataset.json       # Unresolved ticket extraction, priority scores & holiday calendar
├── task3_knowledge_pipeline/
│   └── kb_cicd_pipeline_manifest.json            # Knowledge base document versions, SHA-256 hashes & quarantine logs
├── task4_temporal_rag/
│   └── temporal_rag_policies.json               # Historical & current policies with RBAC, effective dates & citations
├── task5_multimodal_ocr/
│   ├── sample_invoice_ORD1111.png               # High-contrast sample invoice receipt for OCR
│   └── ocr_crossval_ground_truth.json           # OCR ground truth, customer claims & discrepancy benchmarks
└── task6_multilingual_sessions/
    └── multilingual_hinglish_sessions.json      # Hinglish transliteration mappings & 10+ turn memory sessions
```

---

## 📋 Task-by-Task Dataset Specifications

### 1. Task 1: Multilingual Sentiment & Escalation Corpus
- **File**: `task1_sentiment/multilingual_sentiment_escalations.json`
- **Languages**: English, Hindi, Spanish, French, German, Hinglish.
- **Features**: Sarcasm confidence, frustration detection, calm high-risk triggers (legal threats, account compromises, duplicate payments), and after-hours on-call queue assignments.

### 2. Task 2: Structured Tickets & SLA Matrix
- **File**: `task2_tickets_sla/structured_tickets_sla_dataset.json`
- **Features**: Ground truth extraction for customer, order ID, product SKU, issue category, contact info (PII masked), dynamic priority formulas (Severity, Sentiment, Wait time, Impact), and official 2024 corporate holiday exclusions.

### 3. Task 3: Knowledge Base CI/CD Manifest
- **File**: `task3_knowledge_pipeline/kb_cicd_pipeline_manifest.json`
- **Features**: SHA-256 delta fingerprints, pre-activation quality gate benchmarks (Semantic Accuracy >= 90%, Grounding >= 92%), maintenance window timing (01:00-05:00), and quarantined malicious files.

### 4. Task 4: Temporal RAG Policies
- **File**: `task4_temporal_rag/temporal_rag_policies.json`
- **Features**: Versioned policies with metadata (`product_category`, `region`, `access_level`, `effective_date`, `expiry_date`), historical date evaluation benchmark, and exact line citations.

### 5. Task 5: Multimodal OCR & Invoice Benchmark
- **File**: `task5_multimodal_ocr/ocr_crossval_ground_truth.json` & `sample_invoice_ORD1111.png`
- **Features**: Billed amounts, dates, error codes, discrepancy detection benchmarks ($450 claimed vs $350 actual), and retention policies.

### 6. Task 6: Multilingual Hinglish & Session Memory
- **File**: `task6_multilingual_sessions/multilingual_hinglish_sessions.json`
- **Features**: Transliteration lexicon, code-switched dialogues, multi-turn entity preservation across typo corrections, 30-minute inactivity timeouts, and 24-hour summary restoration cache.

---
*Maintained by Parth Biradar for the ElevanceSkills Internship Program.*
