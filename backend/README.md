# Backend

FastAPI backend for the forensic investigation assistant.

## What It Handles

- case creation and case isolation
- dataset upload and summary generation
- semantic column classification
- context-aware query execution
- specialized CDR, tower, IPDR, and cross-dataset analytics
- structured response generation
- DOCX report export

## Main Service Files

- [app/main.py](/Users/hemasai/Documents/AIFOrnsic/backend/app/main.py)
- [app/api/routes.py](/Users/hemasai/Documents/AIFOrnsic/backend/app/api/routes.py)
- [app/core/store.py](/Users/hemasai/Documents/AIFOrnsic/backend/app/core/store.py)
- [app/services/data_loader.py](/Users/hemasai/Documents/AIFOrnsic/backend/app/services/data_loader.py)
- [app/services/analysis.py](/Users/hemasai/Documents/AIFOrnsic/backend/app/services/analysis.py)
- [app/services/forensic_analytics.py](/Users/hemasai/Documents/AIFOrnsic/backend/app/services/forensic_analytics.py)
- [app/services/intent.py](/Users/hemasai/Documents/AIFOrnsic/backend/app/services/intent.py)
- [app/services/query_engine.py](/Users/hemasai/Documents/AIFOrnsic/backend/app/services/query_engine.py)
- [app/services/response_builder.py](/Users/hemasai/Documents/AIFOrnsic/backend/app/services/response_builder.py)
- [app/services/reporting.py](/Users/hemasai/Documents/AIFOrnsic/backend/app/services/reporting.py)

## API Endpoints

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

## Analytics Coverage

### Generic

- top entities
- common entities across datasets
- suspicious pattern scan
- unique entities
- entity drilldown

### CDR

- top outgoing callers
- who called a target and how many times
- pair history
- day/week pattern
- night-call analysis
- burner-style call profile

### Tower

- top tower hits
- co-location detection
- movement reconstruction
- location spread scoring

### IPDR

- VPN usage
- TOR usage
- encrypted app usage
- suspicious IP/host detection
- upload/download anomaly scoring
- burner-style internet profile

### Cross-Dataset / Investigation

- entity profile synthesis
- critical-window reconstruction
- role scoring
- hierarchy inference
- counter-surveillance summary
- final action summary

## Run

```bash
cd /Users/hemasai/Documents/AIFOrnsic/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 sample_data/generate_samples.py
uvicorn app.main:app --reload --port 8000
```

## Environment

Optional AI formatting:

```bash
export AI_API_KEY=your_key
export AI_BASE_URL=https://openrouter.ai/api/v1
export AI_MODEL=openrouter/free
```

## Notes

- all calculations are pandas-based
- AI is not used for core analysis
- responses are normalized before API serialization to handle pandas/numpy values safely
- state is stored in memory only
