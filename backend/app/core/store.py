from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

import pandas as pd


def default_case_context() -> dict[str, Any]:
    return {
        "last_entity": None,
        "last_intent": "overview",
        "last_query_type": None,
        "last_dataset_used": None,
    }


@dataclass
class DatasetRecord:
    file_name: str
    dataframe: pd.DataFrame
    summary: dict[str, Any]
    uploaded_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CaseRecord:
    case_id: str
    case_name: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    datasets: list[DatasetRecord] = field(default_factory=list)
    chat_history: list[dict[str, str]] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=default_case_context)
    observation_items: list[str] = field(default_factory=list)


class InMemoryCaseStore:
    def __init__(self) -> None:
        self.cases: dict[str, CaseRecord] = {}

    def create_case(self, case_name: str) -> CaseRecord:
        case_id = str(uuid4())[:8]
        record = CaseRecord(case_id=case_id, case_name=case_name)
        self.cases[case_id] = record
        return record

    def list_cases(self) -> list[CaseRecord]:
        return sorted(self.cases.values(), key=lambda item: item.created_at, reverse=True)

    def get_case(self, case_id: str) -> CaseRecord | None:
        return self.cases.get(case_id)


case_store = InMemoryCaseStore()
