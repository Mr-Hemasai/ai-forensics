# AI Chatbot for Forensic Analysis of Telecom & Digital Data

Chat-first, case-based forensic analysis platform for telecom and digital datasets. The project is built as a hackathon-ready prototype with a React frontend and a FastAPI backend.

It supports:

- isolated investigation cases
- multi-file CSV/Excel upload per case
- dynamic schema understanding for telecom and digital evidence
- context-aware conversational querying
- specialized CDR, tower, IPDR, and cross-dataset analytics
- structured investigator-style answers
- lightweight visualizations
- DOCX report generation

## Current Scope

This is not a production system. It is a working prototype designed for:

- demos
- hackathons
- investigator workflow simulation
- explainable forensic analysis

It keeps everything in memory and avoids heavy infrastructure.

## Key Features

### Case-Based Investigation Workspace

- Create multiple cases
- Keep datasets, chat history, and context isolated per case
- Switch cases without data overlap

### Universal Dataset Handling

The backend accepts structured telecom and digital datasets such as:

- CDR
- Tower Dump
- IPDR
- other CSV/Excel files with numbers, timestamps, IDs, IPs, and location fields

It automatically classifies columns into categories like:

- entity
- relationship
- time
- location
- metric
- network

### Context-Aware Chatbot

The chatbot maintains per-case conversational context:

- `last_entity`
- `last_intent`
- `last_query_type`
- `last_dataset_used`

This allows follow-up questions such as:

- `to whom`
- `show their night activity`
- `who contacted that number`

### Specialized Forensic Analytics

The backend now includes dataset-specific analytics:

#### CDR

- outgoing call counts by caller
- incoming call analysis by receiver
- exact pair history with timestamps and durations
- night-call analysis
- day-by-day and weekday pattern detection
- burner-style short-window profile analysis

#### Tower

- highest-hit towers
- co-location within configurable time windows
- movement reconstruction
- location spread scoring

#### IPDR

- VPN usage detection
- TOR / dark-web indicator detection
- encrypted messaging app classification
- suspicious IP / suspicious host matching
- upload/download anomaly checks
- burner-style IPDR profile analysis

#### Cross-Dataset

- common entities across datasets
- stitched multi-dataset event timelines
- entity profile synthesis
- critical-window reconstruction

#### Investigation Synthesis

- role scoring
- hierarchy inference
- evidence ranking
- final action summary
- counter-surveillance summary

## Frontend

The UI uses a fixed-screen 3-panel layout:

- left sidebar: case control and observation box
- center panel: chat-first investigation UI
- right sidebar: upload, datasets, visuals, query history, and report action

Current UX features:

- internal panel scrolling only
- fixed chat input at the bottom
- single-row smart suggestion chips
- loading indicators
- query history replay
- last two relevant visualizations only

## Backend API

### Core Endpoints

- `POST /case/create`
- `GET /case/list`
- `GET /case/{case_id}`
- `POST /upload`
- `POST /query`
- `DELETE /dataset`

### Investigation Utilities

- `GET /entity/drilldown`
- `GET /timeline`
- `GET /report/generate`
- `GET /health`

## Main Backend Modules

- [backend/app/services/data_loader.py](/Users/hemasai/Documents/AIFOrnsic/backend/app/services/data_loader.py)
- [backend/app/services/analysis.py](/Users/hemasai/Documents/AIFOrnsic/backend/app/services/analysis.py)
- [backend/app/services/forensic_analytics.py](/Users/hemasai/Documents/AIFOrnsic/backend/app/services/forensic_analytics.py)
- [backend/app/services/intent.py](/Users/hemasai/Documents/AIFOrnsic/backend/app/services/intent.py)
- [backend/app/services/query_engine.py](/Users/hemasai/Documents/AIFOrnsic/backend/app/services/query_engine.py)
- [backend/app/services/response_builder.py](/Users/hemasai/Documents/AIFOrnsic/backend/app/services/response_builder.py)
- [backend/app/services/reporting.py](/Users/hemasai/Documents/AIFOrnsic/backend/app/services/reporting.py)

## Folder Structure

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

## Run Locally

### 1. Backend

```bash
cd /Users/hemasai/Documents/AIFOrnsic/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 sample_data/generate_samples.py
uvicorn app.main:app --reload --port 8000
```

Optional AI formatting:

```bash
export AI_API_KEY=your_key
export AI_BASE_URL=https://openrouter.ai/api/v1
export AI_MODEL=openrouter/free
```

### 2. Frontend

```bash
cd /Users/hemasai/Documents/AIFOrnsic/frontend
npm install
echo "VITE_API_BASE_URL=http://localhost:8000" > .env
npm run dev
```

## Example Queries

### General

- `Show most active entities`
- `Find suspicious activity`
- `Who appears across multiple datasets?`
- `Show their night activity`

### CDR

- `Which phone number made the most calls overall?`
- `Who called 9824942603 and how many times?`
- `Show all calls between 9895822412 and 9824942603`
- `Identify all calls made between 10PM and 6AM`

### Tower

- `Which towers had the highest number of hits?`
- `Were 9895822412 and 9824942603 ever at the same tower at the same time?`
- `Track 9895822412 physical movement across the investigation period`
- `Which suspect has the widest geographic spread across towers?`

### IPDR

- `Which subscribers are using VPN?`
- `Was TOR used by any suspect?`
- `Which suspects use encrypted messaging apps?`
- `Identify all sessions with suspicious external IP addresses`

### Cross-Dataset

- `Build a complete profile of 9895822412 using all three datasets`
- `Reconstruct a timeline of events for the critical window August 1-3`
- `Which suspect is most likely the leader of the network?`
- `Generate a final investigative summary`

## Sample Data

Generate demo datasets with:

```bash
cd /Users/hemasai/Documents/AIFOrnsic/backend
python3 sample_data/generate_samples.py
```

Generated files:

- [backend/sample_data/cdr_sample.csv](/Users/hemasai/Documents/AIFOrnsic/backend/sample_data/cdr_sample.csv)
- [backend/sample_data/tower_dump_sample.csv](/Users/hemasai/Documents/AIFOrnsic/backend/sample_data/tower_dump_sample.csv)
- [backend/sample_data/ipdr_sample.csv](/Users/hemasai/Documents/AIFOrnsic/backend/sample_data/ipdr_sample.csv)

These are simplified demo files. The richer forensic analytics become more useful when real uploaded datasets include:

- domain/app fields in IPDR
- city/location metadata in tower data
- clearer suspect/alias labels
- longer time windows

## Important Notes

- All core calculations are done with pandas
- AI is optional and used only for wording/formatting
- Data is stored in memory only
- No database is used
- Frontend and backend are intentionally lightweight

## Documentation

- Full report: [PROJECT_REPORT.md](/Users/hemasai/Documents/AIFOrnsic/PROJECT_REPORT.md)
- Backend notes: [backend/README.md](/Users/hemasai/Documents/AIFOrnsic/backend/README.md)
- Frontend notes: [frontend/README.md](/Users/hemasai/Documents/AIFOrnsic/frontend/README.md)
