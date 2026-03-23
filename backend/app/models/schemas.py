from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class CaseCreateRequest(BaseModel):
    case_name: str = Field(..., min_length=2, max_length=100)


class QueryRequest(BaseModel):
    case_id: str
    message: str = Field(..., min_length=2)


class DatasetSummary(BaseModel):
    file_name: str
    rows: int
    columns: list[str]
    column_profiles: list[dict[str, Any]]
    semantic_summary: dict[str, Any]
    entity_columns: list[str]
    time_columns: list[str]
    location_columns: list[str]
    dataset_type_guess: str
    stats: dict[str, Any]
    preview_rows: list[dict[str, Any]]


class ChatMessage(BaseModel):
    role: str
    content: str


class CaseSummary(BaseModel):
    case_id: str
    case_name: str
    dataset_count: int
    chat_count: int
    datasets: list[DatasetSummary]
    case_profile: Optional[dict[str, Any]] = None


class CaseDetail(CaseSummary):
    chat_history: list[ChatMessage]
    observation_items: list[str]


class QueryResponse(BaseModel):
    reply: str
    intent: str
    structured_result: dict[str, Any]
    response_card: dict[str, Any]
    suggestions: list[str]
    case_profile: dict[str, Any]
    observation_items: list[str]
    chat_history: list[ChatMessage]
