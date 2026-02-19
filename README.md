# SentinelAI — Enterprise AI Fraud Detection Platform

![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-3.11-blue)
![Next.js](https://img.shields.io/badge/Next.js-14-black)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688)

> **Banking-grade fraud defense platform** that detects AI-generated content, synthetic documents, and deepfake imagery across enterprise communication channels.

---

## 🎯 Problem Statement

Financial institutions face an unprecedented surge in AI-generated fraud — synthetic emails, deepfake documents, and machine-crafted communications that bypass traditional detection. SentinelAI provides a unified investigation platform combining ML models, LLM reasoning, and automated case management to protect banking operations.

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Next.js Frontend                        │
│  Landing │ Dashboard │ Cases │ Analytics │ Clients     │
└────────────────────────────┬────────────────────────────────────┘
                             │ REST API
┌────────────────────────────┴────────────────────────────────────┐
│                        FastAPI Backend                           │
│                                                                  │
│  ┌────────────┐ ┌─────────────┐ ┌──────────────┐ ┌───────────┐ │
│  │ Text       │ │ Document    │ │ Image        │ │ Auth      │ │
│  │ Detection  │ │ Detection   │ │ Detection    │ │ (JWT+RBAC)│ │
│  └─────┬──────┘ └──────┬──────┘ └──────┬───────┘ └───────────┘ │
│        │               │               │                         │
│  ┌─────┴───────────────┴───────────────┴──────────────────────┐ │
│  │              ML Inference Pipeline                          │ │
│  │  AI Detector (sklearn) │ Fraud Detector │ Ollama Mistral   │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────────┐ │
│  │ Risk         │ │ Case         │ │ PDF Report               │ │
│  │ Escalation   │ │ Management   │ │ Generator (reportlab)    │ │
│  └──────────────┘ └──────────────┘ └──────────────────────────┘ │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │ SQLite: audit_logs │ cases │ case_notes │ clients │ users   ││
│  └──────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────┘
```

## ✨ Core Features

### 1. Multi-Modal Fraud Detection
| Channel      | Method                                                    | Models                        |
|-------------|-----------------------------------------------------------|-------------------------------|
| **Text**    | Stylometric analysis, keyword fraud scoring, ML+LLM       | `ai_detector.pkl` + Mistral   |
| **Document**| PDF extraction → text pipeline → fraud signal analysis     | `fraud_detector.pkl` + Mistral|
| **Image**   | Deepfake probability via metadata + pixel analysis         | Statistical heuristics        |

### 2. Case Management System
- **Auto-case creation**: When analysis returns risk ≥ MEDIUM, an investigation case is automatically created
- **Kanban workflow**: OPEN → UNDER_REVIEW → ESCALATED → RESOLVED / FALSE_POSITIVE
- **Investigation timeline**: Threaded notes from analysts with timestamps
- **PDF export**: Generate professional investigation reports with case details, scores, and timeline

### 3. Risk Escalation Engine
Four alert types triggered automatically:
| Alert Type | Trigger | Status |
|---|---|---|
| `critical_risk` | Risk score ≥ 0.8 | ESCALATED |
| `human_crafted_fraud` | Fraud ≥ 0.6 & AI < 0.3 | ESCALATED |
| `synthetic_suspicious` | AI ≥ 0.6 & Fraud < 0.3 | ESCALATED |
| `elevated_risk` | HIGH risk level | OPEN |

### 4. Role-Based Access Control (RBAC)
- **Analyst**: View cases, add notes, run analyses
- **Reviewer**: All analyst actions + resolve/close cases + register clients
- **Admin**: Full access + user management
- JWT authentication with configurable expiry

### 5. Corporate Client Risk Profiles
- Register enterprise clients with industry and contact info
- Aggregated risk summaries (risk distribution, open cases, avg risk score)
- Link cases to clients for organizational fraud tracking

### 6. Fraud Trend Analytics
- Daily fraud detection trends (area chart)
- Risk level distribution (donut chart)
- AI-generated fraud percentage
- Average case resolution time
- Top fraud keywords across flagged analyses
- Case status pipeline overview

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- [Ollama](https://ollama.ai) with Mistral model (`ollama pull mistral`)

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

On first start, the system:
1. Creates the SQLite database with enterprise schema
2. Seeds a default admin user: `admin` / `sentinel`
3. Loads ML models from `ai/models/`

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:3000`

### API Documentation
FastAPI auto-generates interactive docs at `http://localhost:8000/docs`

## 📁 Project Structure

```
SentinelAI/
├── ai/
│   ├── datasets/              # Training datasets (Enron, phishing, credit card)
│   └── models/                # Trained sklearn models
│       ├── ai_detector.pkl    # AI-generated text classifier (F1=1.00)
│       └── fraud_detector.pkl # Fraud text classifier (F1=0.80)
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app + lifespan + router registration
│   │   ├── database.py        # Enterprise DB layer (5 tables, CRUD, analytics)
│   │   ├── routers/
│   │   │   ├── auth.py        # Login / Register / Profile endpoints
│   │   │   ├── text_detection.py   # POST /analyze/text
│   │   │   ├── document_detection.py # POST /analyze/document
│   │   │   ├── image_detection.py   # POST /analyze/image
│   │   │   ├── cases.py       # Case CRUD + PDF export
│   │   │   ├── clients.py     # Client management + risk profiles
│   │   │   ├── analytics.py   # Fraud trend analytics
│   │   │   └── audit.py       # Audit log endpoints
│   │   ├── services/
│   │   │   ├── auth.py        # JWT + bcrypt + RBAC dependencies
│   │   │   ├── escalation.py  # Risk escalation engine (4 alert types)
│   │   │   ├── report_generator.py # PDF case reports (reportlab)
│   │   │   ├── inference.py   # ML + LLM inference pipeline
│   │   │   ├── text_analyzer.py    # Stylometric features
│   │   │   ├── explainability.py   # Human-readable explanations
│   │   │   ├── fraud_scorer.py     # Keyword-based fraud scoring
│   │   │   └── llm_service.py      # Ollama Mistral integration
│   │   └── utils/
│   │       └── preprocessing.py    # Text cleaning, PDF extraction, hashing
│   └── requirements.txt
└── frontend/
    └── src/
        ├── app/
        │   ├── page.tsx           # Landing page
        │   ├── dashboard/page.tsx # Analysis dashboard
        │   ├── cases/page.tsx     # Kanban case board
        │   ├── cases/[id]/page.tsx # Case investigation detail
        │   ├── analytics/page.tsx # Recharts analytics dashboard
        │   └── clients/page.tsx   # Corporate client management
        ├── components/
        │   ├── Sidebar.tsx        # Navigation sidebar
        │   ├── RiskGauge.tsx      # Animated risk gauge
        │   ├── SignalBar.tsx      # Fraud signal indicator
        │   └── FileUpload.tsx     # Drag & drop upload
        └── lib/
            └── api.ts             # Full API client with auth
```

## 🔌 API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | Login → JWT token |
| POST | `/auth/register` | Create user account |
| GET | `/auth/me` | Current user profile |

### Analysis
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/analyze/text` | AI + fraud text analysis |
| POST | `/analyze/document` | PDF document analysis |
| POST | `/analyze/image` | Image deepfake detection |

### Case Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/cases` | List cases (filterable) |
| GET | `/cases/{id}` | Case detail + notes |
| POST | `/cases/create` | Create case manually |
| PATCH | `/cases/{id}/status` | Update status (RBAC) |
| POST | `/cases/{id}/notes` | Add investigation note |
| POST | `/cases/{id}/export` | Generate PDF report |

### Clients
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/clients` | List corporate clients |
| POST | `/clients` | Register client (reviewer+) |
| GET | `/clients/{id}/risk-summary` | Client risk profile |

### Analytics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/analytics/overview` | Fraud trends & metrics |

### System
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/audit/logs` | Audit trail |

## 🔐 Security & Governance

- **JWT Authentication** with configurable secret and 8-hour token expiry
- **RBAC hierarchy**: analyst → reviewer → admin with endpoint-level enforcement
- **Immutable audit trail**: Every analysis logged with hash, scores, and full result
- **Case governance**: Resolved/False Positive status changes require reviewer+ role
- **Content hashing**: SHA-256 fingerprinting for deduplication

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, React 18, TailwindCSS, Recharts, Framer Motion |
| Backend | FastAPI, Python 3.11, async SQLite (aiosqlite) |
| ML/AI | scikit-learn 1.3.2, PyTorch, Transformers |
| LLM | Ollama (Mistral 7B, local inference) |
| Auth | python-jose (JWT), passlib (bcrypt) |
| PDF | ReportLab |
| Database | SQLite (5 tables, enterprise schema) |

## 📊 Investigation Workflow

```
Content Submitted
       │
       ▼
 ML Pipeline Analysis
 (AI detection + Fraud scoring + LLM explanation)
       │
       ▼
 Risk Evaluation ──── LOW → Audit Log only
       │
    MEDIUM+
       │
       ▼
 Auto-Create Case ──── Risk Escalation Engine
       │                   │
       ▼                   ▼
 Investigation Kanban    Alert Classification
 (OPEN → REVIEW →        (critical_risk,
  ESCALATED → RESOLVED)   human_crafted_fraud,
       │                   synthetic_suspicious)
       ▼
 PDF Report Export
```

## 📄 License

MIT License — built for the hackathon.
