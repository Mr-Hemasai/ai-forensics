from __future__ import annotations

import math
from typing import Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
import pandas as pd

from app.core.store import DatasetRecord, case_store
from app.models.schemas import CaseCreateRequest, CaseDetail, CaseSummary, QueryRequest, QueryResponse
from app.services.data_loader import read_uploaded_file, summarize_dataset
from app.services.analysis import build_case_profile, build_entity_drilldown, build_entity_timeline
from app.services.reporting import build_case_report
from app.services.query_engine import run_query


router = APIRouter()


def _json_safe(value: object) -> object:
    if value is None:
        return None
    if isinstance(value, (str, bool, int)):
        return int(value) if type(value) is not int and isinstance(value, int) else value
    if isinstance(value, float):
        numeric_value = float(value)
        return None if math.isnan(numeric_value) or math.isinf(numeric_value) else numeric_value
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]

    # pandas / numpy style scalars and datetimes
    if hasattr(value, "item") and callable(getattr(value, "item")):
        try:
            return _json_safe(value.item())
        except Exception:
            pass
    if isinstance(value, (pd.Timestamp, pd.Timedelta)):
        return value.isoformat()
    if pd.isna(value):
        return None
    return str(value)


@router.post("/case/create")
def create_case(payload: CaseCreateRequest) -> dict[str, str]:
    case_record = case_store.create_case(payload.case_name)
    welcome = f"Case '{case_record.case_name}' created. Upload datasets to begin analysis."
    case_record.chat_history.append({"role": "assistant", "content": welcome})
    return {"case_id": case_record.case_id, "case_name": case_record.case_name, "message": welcome}


@router.get("/case/list", response_model=list[CaseSummary])
def list_cases() -> list[CaseSummary]:
    output: list[CaseSummary] = []
    for case_record in case_store.list_cases():
        datasets = [
            {"file_name": dataset.file_name, "dataframe": dataset.dataframe, "summary": dataset.summary}
            for dataset in case_record.datasets
        ]
        output.append(
            CaseSummary(
                case_id=case_record.case_id,
                case_name=case_record.case_name,
                dataset_count=len(case_record.datasets),
                chat_count=len(case_record.chat_history),
                datasets=_json_safe([dataset.summary for dataset in case_record.datasets]),
                case_profile=_json_safe(build_case_profile(datasets)),
            )
        )
    return output


@router.get("/case/{case_id}", response_model=CaseDetail)
def get_case(case_id: str) -> CaseDetail:
    case_record = case_store.get_case(case_id)
    if not case_record:
        raise HTTPException(status_code=404, detail="Case not found")

    datasets = [
        {"file_name": dataset.file_name, "dataframe": dataset.dataframe, "summary": dataset.summary}
        for dataset in case_record.datasets
    ]

    return CaseDetail(
        case_id=case_record.case_id,
        case_name=case_record.case_name,
        dataset_count=len(case_record.datasets),
        chat_count=len(case_record.chat_history),
        datasets=_json_safe([dataset.summary for dataset in case_record.datasets]),
        case_profile=_json_safe(build_case_profile(datasets)),
        chat_history=_json_safe(case_record.chat_history),
        observation_items=_json_safe(case_record.observation_items),
    )


@router.post("/upload")
async def upload_files(case_id: str, files: list[UploadFile] = File(...)) -> dict[str, object]:
    case_record = case_store.get_case(case_id)
    if not case_record:
        raise HTTPException(status_code=404, detail="Case not found")

    uploaded_summaries: list[dict[str, object]] = []
    for file in files:
        content = await file.read()
        try:
            df = read_uploaded_file(file.filename, content)
            summary = summarize_dataset(file.filename, df)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"{file.filename}: {exc}") from exc

        case_record.datasets.append(DatasetRecord(file_name=file.filename, dataframe=df, summary=summary))
        uploaded_summaries.append(summary)

    assistant_message = f"Uploaded {len(uploaded_summaries)} file(s) into case {case_record.case_name}."
    case_record.chat_history.append({"role": "assistant", "content": assistant_message})
    return {"message": assistant_message, "datasets": _json_safe(uploaded_summaries)}


@router.post("/query", response_model=QueryResponse)
def query_case(payload: QueryRequest) -> QueryResponse:
    case_record = case_store.get_case(payload.case_id)
    if not case_record:
        raise HTTPException(status_code=404, detail="Case not found")

    case_record.chat_history.append({"role": "user", "content": payload.message})
    result = run_query(case_record, payload.message)
    case_record.chat_history.append({"role": "assistant", "content": result["reply"]})

    return QueryResponse(
        reply=result["reply"],
        intent=result["intent"],
        structured_result=_json_safe(result["structured_result"]),
        response_card=_json_safe(result["response_card"]),
        suggestions=_json_safe(result["response_card"].get("suggestions", [])),
        case_profile=_json_safe(result["case_profile"]),
        observation_items=_json_safe(result["observation_items"]),
        chat_history=_json_safe(case_record.chat_history),
        ai_used=bool(result.get("ai_used")),
        ai_provider=_json_safe(result.get("ai_provider")),
        ai_model=_json_safe(result.get("ai_model")),
        ai_error=_json_safe(result.get("ai_error")),
    )


@router.delete("/dataset")
def remove_dataset(case_id: str, file_name: str) -> dict[str, str]:
    case_record = case_store.get_case(case_id)
    if not case_record:
        raise HTTPException(status_code=404, detail="Case not found")

    before = len(case_record.datasets)
    case_record.datasets = [dataset for dataset in case_record.datasets if dataset.file_name != file_name]
    if len(case_record.datasets) == before:
        raise HTTPException(status_code=404, detail="Dataset not found")

    message = f"Removed {file_name} from case {case_record.case_name}."
    case_record.chat_history.append({"role": "assistant", "content": message})
    return {"message": message}


@router.get("/entity/drilldown")
def entity_drilldown(case_id: str, entity: str) -> dict[str, object]:
    case_record = case_store.get_case(case_id)
    if not case_record:
        raise HTTPException(status_code=404, detail="Case not found")
    datasets = [
        {"file_name": dataset.file_name, "dataframe": dataset.dataframe, "summary": dataset.summary}
        for dataset in case_record.datasets
    ]
    return build_entity_drilldown(datasets, entity)


@router.get("/timeline")
def case_timeline(case_id: str, entity: Optional[str] = None) -> dict[str, object]:
    case_record = case_store.get_case(case_id)
    if not case_record:
        raise HTTPException(status_code=404, detail="Case not found")
    datasets = [
        {"file_name": dataset.file_name, "dataframe": dataset.dataframe, "summary": dataset.summary}
        for dataset in case_record.datasets
    ]
    events = build_entity_timeline(datasets, entity, limit=100)
    return {"entity": entity, "events": events}


@router.get("/report/generate")
def generate_report(case_id: str) -> FileResponse:
    case_record = case_store.get_case(case_id)
    if not case_record:
        raise HTTPException(status_code=404, detail="Case not found")
    try:
        report_path = build_case_report(case_record)
    except ImportError as exc:
        raise HTTPException(
            status_code=500,
            detail="Report dependencies missing. Reinstall backend requirements to enable DOCX export.",
        ) from exc
    return FileResponse(
        path=report_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=report_path.name,
    )
