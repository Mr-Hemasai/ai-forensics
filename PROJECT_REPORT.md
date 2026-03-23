# Complete Project Report

## Project Title

AI Chatbot for Forensic Analysis of Telecom & Digital Data

## 1. Executive Summary

This project is a case-based forensic investigation assistant designed for telecom and digital evidence analysis. It is built as a working prototype with a React frontend and a FastAPI backend.

The current system supports:

- isolated investigation cases
- upload of multiple CSV and Excel datasets per case
- dynamic schema understanding
- context-aware conversational analysis
- specialized CDR, tower, IPDR, and cross-dataset analytics
- structured forensic answers
- lightweight visualizations
- DOCX report generation

The project is intended for hackathon and demo use, not production deployment. It is designed to remain lightweight, explainable, and fully data-driven. All actual analysis is done with pandas. AI is optional and used only for wording and formatting.

## 2. Problem Addressed

Investigators often receive separate data sources such as:

- CDR
- tower dump records
- IPDR
- other structured spreadsheets with numbers, timestamps, identifiers, IPs, locations, and volume metrics

The key challenge is not only reading those files but correlating them:

- across entities
- across time
- across location
- across communication and internet activity

This project turns that workflow into a case-based chat system where an investigator can upload data, ask questions, follow up naturally, inspect results, and export a report.

## 3. System Goals

The system was upgraded to behave as:

- a chat-first forensic analysis tool
- a case-based isolated workspace
- a multi-dataset investigation assistant
- a context-aware conversational system
- a data-driven, non-bluffing prototype

## 4. Technology Stack

### Backend

- FastAPI
- Uvicorn
- pandas
- openpyxl
- python-multipart
- httpx
- openai
- python-docx
- matplotlib

### Frontend

- React 18
- Vite
- Tailwind CSS
- lucide-react

## 5. Project Structure

```text
AIFOrnsic/
├── PROJECT_REPORT.md
├── README.md
├── backend/
│   ├── README.md
│   ├── requirements.txt
│   ├── sample_data/
│   │   ├── cdr_sample.csv
│   │   ├── tower_dump_sample.csv
│   │   ├── ipdr_sample.csv
│   │   └── generate_samples.py
│   └── app/
│       ├── main.py
│       ├── api/routes.py
│       ├── core/store.py
│       ├── models/schemas.py
│       └── services/
│           ├── ai_formatter.py
│           ├── analysis.py
│           ├── data_loader.py
│           ├── forensic_analytics.py
│           ├── intent.py
│           ├── query_engine.py
│           ├── reporting.py
│           └── response_builder.py
└── frontend/
    ├── README.md
    ├── package.json
    └── src/
        ├── App.jsx
        ├── styles.css
        ├── lib/api.js
        └── components/
            ├── CaseSidebar.jsx
            ├── ChatPanel.jsx
            ├── DatasetPanel.jsx
            ├── InsightCards.jsx
            ├── RightPanel.jsx
            └── VisualizationPanel.jsx
```

## 6. High-Level Architecture

The application has two layers.

### Frontend Layer

The frontend is responsible for:

- case creation and switching
- file upload
- chat interaction
- suggestion rendering
- visualization display
- query history replay
- report download

### Backend Layer

The backend is responsible for:

- in-memory case storage
- file parsing
- semantic classification of uploaded data
- query intent detection
- conversational context memory
- dataset-specific forensic analytics
- response building
- optional AI wording enhancement
- report generation

## 7. Backend Architecture

### 7.1 Application Entry

File: [backend/app/main.py](/Users/hemasai/Documents/AIFOrnsic/backend/app/main.py)

Responsibilities:

- initialize FastAPI
- configure CORS
- register routes
- expose `/health`

### 7.2 API Layer

File: [backend/app/api/routes.py](/Users/hemasai/Documents/AIFOrnsic/backend/app/api/routes.py)

Endpoints:

- `POST /case/create`
- `GET /case/list`
- `GET /case/{case_id}`
- `POST /upload`
- `POST /query`
- `DELETE /dataset`
- `GET /entity/drilldown`
- `GET /timeline`
- `GET /report/generate`
- `GET /health`

Important implementation detail:

- response payloads are normalized before serialization so pandas and numpy values do not crash FastAPI responses

### 7.3 In-Memory Store

File: [backend/app/core/store.py](/Users/hemasai/Documents/AIFOrnsic/backend/app/core/store.py)

Each case stores:

- case id
- case name
- uploaded datasets
- chat history
- context
- observation items

The store is intentionally simple:

- no database
- no persistence across restart
- no external cache

### 7.4 Schemas

File: [backend/app/models/schemas.py](/Users/hemasai/Documents/AIFOrnsic/backend/app/models/schemas.py)

Defines request and response models for:

- case creation
- dataset summaries
- case detail
- chat messages
- query responses

## 8. Frontend Architecture

### 8.1 Layout

The UI uses a fixed-screen 3-column layout:

- left sidebar
- center chat
- right sidebar

The page does not scroll. Each panel has internal scrolling only.

### 8.2 Main App

File: [frontend/src/App.jsx](/Users/hemasai/Documents/AIFOrnsic/frontend/src/App.jsx)

Responsibilities:

- fetch case list
- load case details
- manage active case
- send queries
- upload/remove datasets
- manage observation items by case
- manage visualization history by case
- trigger report download

### 8.3 Components

#### [CaseSidebar.jsx](/Users/hemasai/Documents/AIFOrnsic/frontend/src/components/CaseSidebar.jsx)

- case creation
- case switcher
- observation box
- active case display

#### [ChatPanel.jsx](/Users/hemasai/Documents/AIFOrnsic/frontend/src/components/ChatPanel.jsx)

- chat rendering
- user/system bubble layout
- fixed bottom input
- single-row suggestion chips
- loading state
- auto-scroll

#### [RightPanel.jsx](/Users/hemasai/Documents/AIFOrnsic/frontend/src/components/RightPanel.jsx)

- upload controls
- dataset list
- visualization history
- query history
- report button

#### [VisualizationPanel.jsx](/Users/hemasai/Documents/AIFOrnsic/frontend/src/components/VisualizationPanel.jsx)

- frequency views
- relationship tables
- cross-dataset views
- suspicious result views

The timeline visual was intentionally removed from the right panel to match the current UI requirement.

## 9. Case-Based Investigation Model

Each investigation is treated as a separate case.

Each case contains:

- its own datasets
- its own chat
- its own context memory
- its own observation history
- its own visualization history

This guarantees:

- no case-to-case data mixing
- no conversation overlap
- context-aware follow-ups only within the selected case

## 10. Universal Dataset Handling

File: [backend/app/services/data_loader.py](/Users/hemasai/Documents/AIFOrnsic/backend/app/services/data_loader.py)

### 10.1 Supported File Types

- CSV
- XLSX
- XLS

### 10.2 Column Classification

The backend inspects both column names and values.

It classifies columns into semantic types such as:

- phone number
- IP address
- IMEI
- IMSI
- device ID
- user ID
- tower ID
- city
- location label
- timestamp
- duration
- volume
- upload volume
- download volume
- application
- domain
- port

It also classifies columns into categories such as:

- entity
- relationship
- time
- location
- metric
- network

### 10.3 Relationship Pair Detection

The loader attempts to identify true source-target pairs, especially for telecom-style data such as:

- caller -> receiver
- sender -> receiver

### 10.4 Dataset Type Guess

The loader infers:

- `cdr`
- `tower_dump`
- `ipdr`
- `generic_structured_data`

## 11. Conversational Context System

Files:

- [backend/app/core/store.py](/Users/hemasai/Documents/AIFOrnsic/backend/app/core/store.py)
- [backend/app/services/intent.py](/Users/hemasai/Documents/AIFOrnsic/backend/app/services/intent.py)
- [backend/app/services/query_engine.py](/Users/hemasai/Documents/AIFOrnsic/backend/app/services/query_engine.py)

Each case maintains:

- `last_entity`
- `last_intent`
- `last_query_type`
- `last_dataset_used`

This enables follow-up queries like:

- `to whom`
- `show their night activity`
- `who contacted that number`

The backend extracts explicit entities from user text and only falls back to prior context when the query clearly refers to a prior entity.

## 12. General Analysis Engine

File: [backend/app/services/analysis.py](/Users/hemasai/Documents/AIFOrnsic/backend/app/services/analysis.py)

The general engine provides:

- top entity frequency
- time-pattern analysis
- repeated pair detection
- cross-dataset overlap detection
- unique entity counts
- median-based outlier detection
- suspicious pattern scan
- entity drilldown
- timeline construction

These are generic, schema-flexible analytics used when the query is broad.

## 13. Specialized Forensic Analytics

File: [backend/app/services/forensic_analytics.py](/Users/hemasai/Documents/AIFOrnsic/backend/app/services/forensic_analytics.py)

This module was added to move the project closer to investigator-style query banks.

### 13.1 CDR Analytics

Implemented:

- outgoing call ranking by caller
- incoming call analysis by receiver
- exact pair history with timestamps and durations
- night-call extraction
- day-by-day and weekday pattern detection
- burner-style short-window CDR profile

These support questions such as:

- who made the most calls
- who called a given number
- what is the pattern between two numbers
- who are the key actors in late-night communication

### 13.2 Tower Analytics

Implemented:

- tower hit ranking
- co-location detection within a configurable time window
- movement reconstruction for a selected entity
- geographic spread scoring

These support questions such as:

- which tower had the highest activity
- were two numbers at the same tower at the same time
- how did an entity move across the dataset
- who has the widest location spread

### 13.3 IPDR Analytics

Implemented:

- VPN indicator detection
- TOR / dark-web indicator detection
- encrypted messaging app classification
- suspicious IP and host matching
- upload/download anomaly detection
- burner-style IPDR profile analysis

These depend on the uploaded data containing relevant IPDR fields such as:

- domain or host
- application name
- port
- upload/download or total transfer metrics

### 13.4 Cross-Dataset Analytics

Implemented:

- stitched event collection across CDR, tower, and IPDR
- complete entity profile synthesis
- critical-window reconstruction

### 13.5 Investigation Synthesis

Implemented:

- role scoring
- hierarchy inference
- evidence ranking
- final action summary
- counter-surveillance summary

These are heuristic and data-driven. They combine:

- call volume
- dataset overlap
- movement spread
- flagged internet activity
- suspicious pattern results

## 14. Query Understanding

File: [backend/app/services/intent.py](/Users/hemasai/Documents/AIFOrnsic/backend/app/services/intent.py)

The current intent system supports:

- general intent categories
- query-type routing
- entity extraction
- date-window extraction
- burner-entity inference trigger

It can now route queries into families such as:

- CDR-specific
- tower-specific
- IPDR-specific
- cross-dataset profile
- critical-window reconstruction
- investigation summary

## 15. Query Orchestration

File: [backend/app/services/query_engine.py](/Users/hemasai/Documents/AIFOrnsic/backend/app/services/query_engine.py)

Responsibilities:

- build case profile
- detect intent
- choose the correct analytics path
- reuse context where appropriate
- provide smart fallback if the entity is missing
- build response card
- update observation items
- update conversational context

This is the central controller that ties together:

- generic analytics
- specialized forensic analytics
- context memory
- response generation

## 16. Response Format

File: [backend/app/services/response_builder.py](/Users/hemasai/Documents/AIFOrnsic/backend/app/services/response_builder.py)

Current response structure:

- Title
- Direct Answer
- Supporting Data
- Analysis
- Insight
- Recommended Action
- `[LEAD]`
- `[ALERT]`

If prior context is used, the response also includes:

- `Context Used: <entity>`

The response builder also supports override-based formatting so specialized analytics can return tailored answers without changing the frontend contract.

## 17. AI Usage

File: [backend/app/services/ai_formatter.py](/Users/hemasai/Documents/AIFOrnsic/backend/app/services/ai_formatter.py)

AI is optional.

It is used only for:

- wording cleanup
- explanation improvement
- simple-English reformulation

AI is not used for:

- calculations
- scoring
- matching
- timeline building
- suspicious detection

Environment variables:

- `AI_API_KEY`
- `AI_BASE_URL`
- `AI_MODEL`

## 18. Report Generation

File: [backend/app/services/reporting.py](/Users/hemasai/Documents/AIFOrnsic/backend/app/services/reporting.py)

The system generates a DOCX report that includes:

1. case details
2. dataset summary
3. investigation summary
4. chat history
5. observation items
6. insights, leads, and alerts
7. generated visuals

## 19. Smart Suggestions

Suggestions are driven by:

- dataset semantics
- current case profile
- latest query result
- response card suggestions

Examples:

- Find top phone numbers
- Show late night phone activity
- Show suspicious numbers
- Find common entities across datasets
- Show related contacts

## 20. Visualizations

Current visual behaviors:

- show only when relevant
- keep only the last two visualization states per case
- do not show fake visuals

Supported visual result types include:

- frequency charts
- ranked relationship tables
- common-entity tables
- suspicious result views

## 21. Sample Data

Files:

- [backend/sample_data/cdr_sample.csv](/Users/hemasai/Documents/AIFOrnsic/backend/sample_data/cdr_sample.csv)
- [backend/sample_data/tower_dump_sample.csv](/Users/hemasai/Documents/AIFOrnsic/backend/sample_data/tower_dump_sample.csv)
- [backend/sample_data/ipdr_sample.csv](/Users/hemasai/Documents/AIFOrnsic/backend/sample_data/ipdr_sample.csv)
- [backend/sample_data/generate_samples.py](/Users/hemasai/Documents/AIFOrnsic/backend/sample_data/generate_samples.py)

The sample datasets are useful for:

- layout verification
- generic analytics
- basic CDR, tower, and IPDR flow testing

They are still simplified compared with rich real-world forensic datasets. For example:

- current IPDR samples do not include rich domain/app/TOR/VPN fields
- current tower samples do not include city-level metadata

This means some advanced modules correctly return no-indicator answers on demo data, but they are ready for richer uploads.

## 22. Example Supported Queries

### General

- Show most active entities
- Find suspicious activity
- Who appears across multiple datasets?

### CDR

- Which phone number made the most calls overall?
- Who called 9824942603 and how many times?
- Show all calls between 9895822412 and 9824942603
- Identify all calls made between 10PM and 6AM

### Tower

- Which towers had the highest number of hits?
- Were 9895822412 and 9824942603 ever at the same tower at the same time?
- Track 9895822412 physical movement across the investigation period
- Which suspect has the widest geographic spread across towers?

### IPDR

- Which subscribers are using VPN?
- Was TOR used by any suspect?
- Which suspects use encrypted messaging apps?
- Identify all sessions with suspicious external IP addresses

### Cross-Dataset / Investigation

- Build a complete profile of 9895822412 using all three datasets
- Reconstruct a timeline of events for the critical window August 1-3
- Which suspect is most likely the leader of the network?
- Is there any evidence of counter-surveillance techniques?
- Generate a final investigative summary

## 23. Setup

### Backend

```bash
cd /Users/hemasai/Documents/AIFOrnsic/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 sample_data/generate_samples.py
uvicorn app.main:app --reload --port 8000
```

Optional AI config:

```bash
export AI_API_KEY=your_key
export AI_BASE_URL=https://openrouter.ai/api/v1
export AI_MODEL=openrouter/free
```

### Frontend

```bash
cd /Users/hemasai/Documents/AIFOrnsic/frontend
npm install
echo "VITE_API_BASE_URL=http://localhost:8000" > .env
npm run dev
```

## 24. Strengths

- case isolation works well
- chat context is maintained per case
- analytics are deterministic
- specialized forensic queries are now supported
- report generation is built in
- UI is demo-friendly and investigation-oriented
- no database is required

## 25. Current Limitations

- all data is in memory only
- no authentication
- no persistence across restart
- some advanced modules require richer real-world datasets to be fully useful
- hierarchy and evidence synthesis are heuristic, not legal conclusions
- no full network graph UI yet

## 26. Final Status

The project is now significantly more capable than the initial generic chatbot prototype.

It supports:

- general forensic analytics
- specialized telecom/digital analytics
- conversational follow-ups
- cross-dataset reasoning
- investigation-oriented summaries

It remains lightweight and hackathon-feasible while being much closer to a realistic forensic demo application.
