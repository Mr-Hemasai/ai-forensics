# AI Chatbot for Forensic Analysis of Telecom & Digital Data

A chat-first forensic investigation platform for analyzing telecom and digital datasets using contextual AI-assisted workflows.

Built as a full-stack prototype using **React** and **FastAPI**, the platform is designed for investigator-style workflows involving:

- telecom data analysis
- multi-dataset intelligence reconstruction
- contextual querying
- suspicious activity detection
- timeline reconstruction
- evidence synthesis
- lightweight investigative reporting

The system focuses on operational investigation workflows rather than generic chatbot interactions.

---

# Overview

The platform allows investigators to:

- create isolated investigation cases
- upload multiple telecom/digital datasets
- analyze CDR, Tower Dump, and IPDR records
- perform contextual conversational analysis
- reconstruct entity relationships and timelines
- generate structured investigation summaries

Unlike generic document-chat systems, this project combines:

- dataset-aware analytics
- contextual memory
- rule-based forensic logic
- conversational investigation workflows

---

# Key Features

## Case-Based Investigation Workspace

- Multiple isolated investigation cases
- Per-case dataset separation
- Independent chat memory/context
- Context switching without data overlap

---

## Universal Dataset Handling

Supports structured telecom and digital evidence datasets such as:

- CDR (Call Detail Records)
- Tower Dump
- IPDR (Internet Protocol Detail Records)
- Generic CSV/Excel datasets

The backend dynamically classifies columns into categories like:

- entity
- relationship
- time
- location
- network
- metric

This allows the system to adapt to different investigation datasets automatically.

---

# Context-Aware Investigation Chatbot

The chatbot maintains conversational investigation context using:

- `last_entity`
- `last_intent`
- `last_query_type`
- `last_dataset_used`

This enables natural investigative follow-up queries such as:

```text
to whom
show their night activity
who contacted that number
```

The goal is to simulate investigator-style workflow continuity rather than isolated prompts.

---

# Specialized Forensic Analytics

## CDR Analytics

- outgoing call frequency analysis
- incoming call analysis
- pairwise communication history
- night activity detection
- weekday behavioral patterns
- burner-style communication analysis

### Example Queries

```text
Which phone number made the most calls overall?
Show all calls between 9895822412 and 9824942603
Identify all calls made between 10PM and 6AM
```

---

## Tower Dump Analytics

- tower hit frequency
- co-location detection
- movement reconstruction
- geographic spread analysis

### Example Queries

```text
Which towers had the highest number of hits?
Were two suspects at the same tower during the same time window?
Track suspect movement across the investigation period
```

---

## IPDR Analytics

- VPN usage detection
- TOR activity indicators
- encrypted messaging app classification
- suspicious IP/domain detection
- upload/download anomaly analysis

### Example Queries

```text
Which subscribers are using VPN?
Was TOR used by any suspect?
Identify suspicious external IP activity
```

---

## Cross-Dataset Intelligence

- entity correlation across datasets
- stitched investigation timelines
- profile synthesis
- critical-window reconstruction

### Example Queries

```text
Build a complete profile of a suspect using all datasets
Reconstruct events between August 1-3
Which suspect appears most central to the network?
```

---

## Investigation Synthesis

The backend also supports higher-level investigative reasoning such as:

- role scoring
- hierarchy inference
- evidence prioritization
- investigative summaries
- counter-surveillance indicators

---

# Frontend

The frontend uses a fixed-screen 3-panel investigation layout.

## Layout

### Left Sidebar

- case controls
- observations
- quick investigation notes

### Center Panel

- chat-first investigation interface
- contextual query flow
- smart suggestions

### Right Sidebar

- dataset uploads
- lightweight visualizations
- query history
- report generation

---

# UX Features

- fixed chat input
- internal panel scrolling
- smart suggestion chips
- query replay
- loading indicators
- contextual investigation flow
- lightweight chart rendering

---

# Backend API

## Core Endpoints

```http
POST /case/create
GET  /case/list
GET  /case/{case_id}
POST /upload
POST /query
DELETE /dataset
```

## Investigation Utilities

```http
GET /entity/drilldown
GET /timeline
GET /report/generate
GET /health
```

---

# Core Backend Modules

```text
backend/app/services/
├── analysis.py
├── data_loader.py
├── forensic_analytics.py
├── intent.py
├── query_engine.py
├── reporting.py
└── response_builder.py
```

---

# Tech Stack

## Frontend

- React
- JavaScript
- Vite

## Backend

- FastAPI
- Pandas
- Python

## Optional AI Layer

- OpenRouter/OpenAI-compatible APIs

---

# Project Structure

```text
AIFOrnsic/
├── PROJECT_REPORT.md
├── README.md
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   └── services/
│   ├── sample_data/
│   ├── requirements.txt
│   └── README.md
└── frontend/
    ├── src/
    │   ├── components/
    │   └── lib/
    ├── package.json
    └── README.md
```

---

# Run Locally

## Backend Setup

```bash
cd backend

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

python3 sample_data/generate_samples.py

uvicorn app.main:app --reload --port 8000
```

---

## Optional AI Formatting Layer

```bash
export AI_API_KEY=your_key
export AI_BASE_URL=https://openrouter.ai/api/v1
export AI_MODEL=openrouter/free
```

AI is optional and currently used only for:

- response wording
- formatting improvements

All core investigation logic runs independently.

---

## Frontend Setup

```bash
cd frontend

npm install

echo "VITE_API_BASE_URL=http://localhost:8000" > .env

npm run dev
```

---

# Sample Data

Generate demo datasets using:

```bash
cd backend
python3 sample_data/generate_samples.py
```

Generated demo files include:

```text
backend/sample_data/cdr_sample.csv
backend/sample_data/tower_dump_sample.csv
backend/sample_data/ipdr_sample.csv
```

---

# Design Goals

This project intentionally prioritizes:

- workflow clarity
- explainable analytics
- contextual querying
- lightweight infrastructure
- rapid experimentation

It is designed as:

- a hackathon-ready prototype
- an investigation workflow simulator
- an AI-assisted forensic analysis system

---

# Important Notes

- All calculations are performed using Pandas
- No database is currently used
- All data remains in memory
- AI usage is optional
- Frontend and backend are intentionally lightweight

---

# Future Improvements

Potential next steps include:

- vector-based contextual retrieval
- persistent case storage
- graph visualization
- entity relationship graphs
- multi-agent investigation workflows
- real-time collaboration
- advanced timeline intelligence
- deployment pipeline
- authentication/role systems

---

# Screenshots
<img width="1470" height="956" alt="Screenshot 2026-03-22 at 11 44 26 PM" src="https://github.com/user-attachments/assets/859c47af-76e8-4b17-90f4-fa022b24ae99" />
<img width="1470" height="956" alt="Screenshot 2026-03-22 at 11 44 49 PM" src="https://github.com/user-attachments/assets/6ba17647-2d91-4ddd-8a8e-832089f65203" />


---

# Documentation

Additional project notes:

- `PROJECT_REPORT.md`
- `backend/README.md`
- `frontend/README.md`

---

# Disclaimer

This project is a prototype built for:

- experimentation
- demonstrations
- workflow simulation
- forensic AI exploration

It is not intended for production forensic deployment.

