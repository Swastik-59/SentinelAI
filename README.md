# SentinelAI — Enterprise AI Fraud Investigation Platform

![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-3.11-blue)
![Next.js](https://img.shields.io/badge/Next.js-14-black)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688)

SentinelAI is a banking-grade fraud investigation platform designed to detect AI-generated phishing content, synthetic documents, and manipulated media across enterprise communication channels.

It combines machine learning detection, fraud-intent scoring, LLM-assisted explanations, and structured case management into a unified workflow system tailored for financial institutions.

---

## Executive Summary

AI-generated fraud is evolving faster than traditional rule-based filters can respond. Financial institutions now face:

- Synthetic phishing emails crafted by large language models  
- AI-assisted payment redirection scams  
- Hybrid attacks blending human-written and AI-generated content  
- Deepfake-based identity manipulation  

SentinelAI addresses this challenge by combining:

- AI-generation detection  
- Fraud-intent classification  
- Policy-based escalation logic  
- Investigation case lifecycle management  
- Compliance-ready audit logging  

This is not just a detection engine — it is a fraud investigation assistant aligned with banking operations.

---

## Intended Users

SentinelAI is designed for:

- Fraud investigation teams  
- Corporate banking relationship managers  
- Compliance officers  
- Security operations teams  
- Risk governance departments  

Instead of manually evaluating suspicious content, users can:

1. Submit content for analysis  
2. Receive AI and fraud probability scores  
3. Review highlighted suspicious signals  
4. Escalate through a structured workflow  
5. Generate investigation-ready reports  

This reduces manual investigation time and improves decision confidence.

---

## Real-World Scenario

A corporate client forwards an urgent email requesting a change in payment instructions.

Traditional approach:
- Manual tone review  
- Sender verification  
- Escalation if unsure  

With SentinelAI:
- Instant AI-generation and fraud scoring  
- Highlighted suspicious phrases  
- Structured risk classification  
- Automatic case creation for policy-level risks  
- Full investigation timeline tracking  

This ensures consistent and auditable decision-making.

---

## System Architecture

┌─────────────────────────────────────────────────────────────────┐
│ Next.js Frontend │
│ Dashboard │ Cases │ Analytics │ Clients │ Governance │
└────────────────────────────┬────────────────────────────────────┘
│ REST API
┌────────────────────────────┴────────────────────────────────────┐
│ FastAPI Backend                                                  │
│                                                                  │
│ Text │ Document │ Image │ Auth (JWT + RBAC)                      │
│                                                                  │
│ ML Inference Pipeline                                            │
│ - AI Detector (sklearn)                                          │
│ - Fraud Detector (sklearn)                                       │
│ - Stylometric Analysis                                           │
│ - Keyword Fraud Signals                                          │
│ - Ollama Mistral (LLM Explanation)                               │
│                                                                  │
│ Risk Escalation Engine                                           │
│ Case Management System                                           │
│ PDF Report Generator                                             │
│                                                                  │
│ SQLite Enterprise Schema                                         │
│ audit_logs │ cases │ case_notes │ clients │ users                │
└──────────────────────────────────────────────────────────────────┘


---

## Core Capabilities

### Multi-Modal Fraud Detection

Text Channel:
- Stylometric feature extraction  
- AI-generation classification  
- Fraud-intent keyword scoring  
- Risk fusion logic  

Document Channel:
- PDF extraction  
- Full text fraud pipeline  
- Metadata inspection  

Image Channel:
- Deepfake probability estimation  
- Pixel-level statistical analysis  

---

## Risk Scoring Framework

Risk formula:

risk_score = (0.6 × fraud_probability) + (0.4 × ai_probability)

Risk Levels:

| Level     | Score Range | Recommended Action |
|-----------|-------------|-------------------|
| LOW       | 0.0 – 0.3   | Log only |
| MEDIUM    | 0.3 – 0.6   | Manual review |
| HIGH      | 0.6 – 0.8   | Strong review |
| CRITICAL  | 0.8 – 1.0   | Immediate escalation |

Escalation types:
- critical_risk  
- human_crafted_fraud  
- synthetic_suspicious  
- elevated_risk  

---

## Case Management Lifecycle

OPEN → UNDER_REVIEW → ESCALATED → RESOLVED / FALSE_POSITIVE

Features:
- Auto-case creation for MEDIUM+ risk  
- Investigator assignment  
- Threaded notes with timestamps  
- Timeline tracking  
- One-click PDF export  

---

## Corporate Client Risk Profiles

- Link cases to enterprise clients  
- Aggregate risk trends per client  
- Track repeated fraud attempts  
- View risk distribution summaries  

---

## Fraud Trend Analytics

Dashboard metrics include:

- Daily fraud detection trends  
- AI-generated fraud percentage  
- Risk distribution charts  
- Average case resolution time  
- Top fraud signals  
- Case pipeline overview  

---

## Governance and Security

- JWT authentication  
- Role-Based Access Control (Analyst, Reviewer, Admin)  
- Endpoint-level authorization  
- SHA-256 content hashing  
- Immutable audit trail  
- Controlled case resolution permissions  

---

## Technical Stack

Frontend:
- Next.js 14  
- React 18  
- TailwindCSS  
- Recharts  

Backend:
- FastAPI  
- Python 3.11  
- Async SQLite  

ML:
- scikit-learn  
- Stylometric feature extraction  

Deepfake:
- PyTorch + heuristic analysis  

LLM:
- Ollama (Mistral 7B, local inference)  

Auth:
- python-jose (JWT)  
- passlib (bcrypt)  

Reporting:
- ReportLab  

Database:
- SQLite enterprise schema  

---

## Dataset Sources

- Enron Email Dataset (corporate baseline)  
- Phishing Email Dataset (fraud patterns)  
- AI vs Human Text Dataset (AI detection)  
- Deepfake datasets (image manipulation detection)  

Training uses sampled subsets for real-time inference performance.

---

## Deployment

Backend:

cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

Frontend:

cd frontend
npm install
npm run dev

Ollama:

ollama pull mistral
ollama serve

---

## Investigation Workflow

Content Submitted
        │
        ▼
 ML + Fraud Analysis
        │
        ▼
 Risk Evaluation
        │
 LOW → Audit Log Only
        │
 MEDIUM+
        │
        ▼
 Auto-Create Case
        │
        ▼
 Escalation Logic
        │
        ▼
 Investigation & Resolution
        │
        ▼
 PDF Report Export

---

## Design Philosophy

SentinelAI emphasizes:

- Decision support over blind automation  
- Explainability over opacity  
- Governance over novelty  
- Workflow integration over isolated prediction  

---

## License

MIT License  
Built as an enterprise-ready hackathon proof-of-concept.

EOF
