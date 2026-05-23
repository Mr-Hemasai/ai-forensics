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

Add screenshots or demo GIFs here:

```text
docs/screenshots/dashboard.png
docs/screenshots/chat.png
docs/screenshots/analytics.png
```

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
* Create and manage multiple investigation cases
* Maintain isolated datasets and conversational context per case
* Switch between investigations without data overlap

Each case preserves:

* uploaded datasets
* query history
* contextual investigation state
* generated findings

⸻

Universal Dataset Handling

The backend supports structured telecom and digital evidence datasets including:

* CDR (Call Detail Records)
* Tower Dumps
* IPDR (Internet Protocol Detail Records)
* Generic CSV/Excel datasets

The ingestion pipeline automatically classifies columns into categories such as:

* entity
* relationship
* time
* location
* network
* metric

This allows flexible querying even across partially inconsistent datasets.

⸻

Context-Aware Conversational Querying

The chatbot maintains investigation context per case using:

* last_entity
* last_intent
* last_query_type
* last_dataset_used

This enables natural follow-up queries such as:

Show their night activity
Who contacted that number?
Was the same suspect seen near this tower?
Build a profile using all datasets

The goal is to simulate investigator-style iterative analysis rather than simple one-shot querying.

⸻

Specialized Forensic Analytics

CDR Analytics

* outgoing/incoming call analysis
* pairwise communication history
* timestamp and duration analysis
* night-call detection
* weekday pattern analysis
* burner-style short-window behavior detection

⸻

Tower Dump Analytics

* highest-hit tower detection
* co-location analysis
* movement reconstruction
* geographic spread scoring
* temporal overlap analysis

⸻

IPDR Analytics

* VPN usage detection
* TOR/dark-web indicators
* encrypted messaging app identification
* suspicious IP/domain matching
* upload/download anomaly checks
* burner-style network profiling

⸻

Cross-Dataset Intelligence

* entity correlation across datasets
* unified timeline reconstruction
* profile synthesis
* critical-window investigation reconstruction
* evidence stitching

⸻

Investigation Synthesis

The system can generate higher-level investigative summaries including:

* role scoring
* hierarchy inference
* evidence ranking
* counter-surveillance indicators
* final action summaries

⸻

Frontend

The frontend uses a fixed-screen 3-panel investigation layout.

Layout Structure

Left Sidebar

* case management
* observation notes
* investigation controls

Center Panel

* conversational investigation interface
* contextual chat workflows
* smart suggestions

Right Sidebar

* dataset uploads
* analytics visualizations
* query history
* report generation

⸻

UX Features

* fixed chat input
* internal panel scrolling
* contextual suggestion chips
* lightweight visualizations
* loading indicators
* query replay support
* recent visualization tracking

⸻

Backend Architecture

Core API Endpoints

Case Management

POST /case/create
GET /case/list
GET /case/{case_id}

Dataset Operations

POST /upload
DELETE /dataset

Query & Analysis

POST /query
GET /timeline
GET /entity/drilldown

Reporting

GET /report/generate

System

GET /health

⸻

Core Backend Modules

backend/app/services/
├── analysis.py
├── data_loader.py
├── forensic_analytics.py
├── intent.py
├── query_engine.py
├── reporting.py
└── response_builder.py

⸻

High-Level Architecture

Frontend (React)
        ↓
FastAPI Backend
        ↓
Intent Detection Layer
        ↓
Query Engine
        ↓
Forensic Analytics Engine
        ↓
Response Builder / Reporting

⸻

Tech Stack

Frontend

* React
* Vite
* JavaScript
* CSS

Backend

* FastAPI
* Pandas
* Python

Optional AI Layer

* OpenRouter/OpenAI-compatible APIs

⸻

Folder Structure

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

⸻

Run Locally

1. Backend Setup

cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 sample_data/generate_samples.py
uvicorn app.main:app --reload --port 8000

⸻

Optional AI Formatting Layer

export AI_API_KEY=your_key
export AI_BASE_URL=https://openrouter.ai/api/v1
export AI_MODEL=openrouter/free

AI is optional and used only for:

* wording refinement
* response formatting
* structured investigator summaries

Core analytics are rule-based and implemented with pandas.

⸻

2. Frontend Setup

cd frontend
npm install
echo "VITE_API_BASE_URL=http://localhost:8000" > .env
npm run dev

⸻

Example Investigation Queries

General Queries

Show most active entities
Find suspicious activity
Who appears across multiple datasets?
Show their night activity

⸻

CDR Queries

Which phone number made the most calls overall?
Who called 9824942603 and how many times?
Show all calls between 9895822412 and 9824942603
Identify all calls made between 10PM and 6AM

⸻

Tower Queries

Which towers had the highest number of hits?
Were 9895822412 and 9824942603 ever at the same tower?
Track suspect movement across the investigation period
Which suspect has the widest geographic spread?

⸻

IPDR Queries

Which subscribers are using VPN?
Was TOR used by any suspect?
Which suspects use encrypted messaging apps?
Identify sessions with suspicious external IP addresses

⸻

Cross-Dataset Queries

Build a complete profile using all datasets
Reconstruct a timeline for the critical window
Which suspect is most likely the leader?
Generate a final investigative summary

⸻

Sample Data

Generate demo datasets:

cd backend
python3 sample_data/generate_samples.py

Generated demo files:

backend/sample_data/cdr_sample.csv
backend/sample_data/tower_dump_sample.csv
backend/sample_data/ipdr_sample.csv

These are simplified datasets intended for testing workflows and analytics behavior.

⸻

Current Limitations

This is a prototype system and currently has several limitations:

* datasets stored entirely in memory
* no authentication or RBAC
* no persistent database
* limited scalability
* lightweight visualization layer
* simplified forensic heuristics

The focus is experimentation and workflow simulation rather than production deployment.

⸻

Future Improvements

Potential next steps include:

* vector-based contextual retrieval
* graph database integration
* persistent case memory
* multi-agent investigation workflows
* advanced visualization dashboards
* streaming analytics
* collaborative investigations
* evidence chain management
* deployment-ready infrastructure

⸻

Documentation

Additional documentation:

* PROJECT_REPORT.md
* backend/README.md
* frontend/README.md

⸻

License

Prototype project for educational, research, and demonstration purposes.
