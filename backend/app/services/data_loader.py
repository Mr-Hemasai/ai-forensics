from __future__ import annotations

import re
import warnings
from io import BytesIO
from typing import Any

import pandas as pd


PHONE_PATTERN = re.compile(r"^\+?\d{10,15}$")
IPV4_PATTERN = re.compile(r"^(?:\d{1,3}\.){3}\d{1,3}$")
IMEI_PATTERN = re.compile(r"^\d{14,16}$")
IMSI_PATTERN = re.compile(r"^\d{14,16}$")
LAT_PATTERN = re.compile(r"^-?\d{1,2}\.\d+$")
LON_PATTERN = re.compile(r"^-?\d{1,3}\.\d+$")

NAME_HINTS: dict[str, dict[str, str]] = {
    "phone": {"semantic_type": "phone_number", "category": "entity"},
    "mobile": {"semantic_type": "phone_number", "category": "entity"},
    "msisdn": {"semantic_type": "phone_number", "category": "entity"},
    "caller": {"semantic_type": "phone_number", "category": "relationship", "role": "source"},
    "callee": {"semantic_type": "phone_number", "category": "relationship", "role": "target"},
    "receiver": {"semantic_type": "phone_number", "category": "relationship", "role": "target"},
    "sender": {"semantic_type": "phone_number", "category": "relationship", "role": "source"},
    "number": {"semantic_type": "phone_number", "category": "entity"},
    "ip": {"semantic_type": "ip_address", "category": "entity"},
    "host": {"semantic_type": "domain", "category": "network"},
    "domain": {"semantic_type": "domain", "category": "network"},
    "url": {"semantic_type": "domain", "category": "network"},
    "site": {"semantic_type": "domain", "category": "network"},
    "app": {"semantic_type": "application", "category": "network"},
    "application": {"semantic_type": "application", "category": "network"},
    "service": {"semantic_type": "application", "category": "network"},
    "platform": {"semantic_type": "application", "category": "network"},
    "port": {"semantic_type": "port", "category": "network"},
    "imei": {"semantic_type": "imei", "category": "entity"},
    "imsi": {"semantic_type": "imsi", "category": "entity"},
    "device": {"semantic_type": "device_id", "category": "entity"},
    "user": {"semantic_type": "user_id", "category": "entity"},
    "account": {"semantic_type": "user_id", "category": "entity"},
    "tower": {"semantic_type": "tower_id", "category": "location"},
    "cell": {"semantic_type": "tower_id", "category": "location"},
    "site": {"semantic_type": "tower_id", "category": "location"},
    "sector": {"semantic_type": "location_zone", "category": "location"},
    "location": {"semantic_type": "location_label", "category": "location"},
    "city": {"semantic_type": "city", "category": "location"},
    "district": {"semantic_type": "district", "category": "location"},
    "state": {"semantic_type": "state", "category": "location"},
    "lat": {"semantic_type": "latitude", "category": "location"},
    "lon": {"semantic_type": "longitude", "category": "location"},
    "lng": {"semantic_type": "longitude", "category": "location"},
    "time": {"semantic_type": "timestamp", "category": "time"},
    "date": {"semantic_type": "timestamp", "category": "time"},
    "timestamp": {"semantic_type": "timestamp", "category": "time"},
    "start": {"semantic_type": "timestamp", "category": "time"},
    "end": {"semantic_type": "timestamp", "category": "time"},
    "duration": {"semantic_type": "duration", "category": "metric"},
    "bytes": {"semantic_type": "volume", "category": "metric"},
    "upload": {"semantic_type": "upload_volume", "category": "metric"},
    "download": {"semantic_type": "download_volume", "category": "metric"},
}


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    normalized.columns = [str(column).strip() for column in normalized.columns]
    return normalized


def read_uploaded_file(file_name: str, content: bytes) -> pd.DataFrame:
    lower_name = file_name.lower()
    if lower_name.endswith(".csv"):
        df = pd.read_csv(BytesIO(content))
    elif lower_name.endswith((".xlsx", ".xls")):
        df = pd.read_excel(BytesIO(content))
    else:
        raise ValueError("Unsupported file type. Upload CSV or Excel files only.")
    return normalize_columns(df)


def _series_examples(series: pd.Series, limit: int = 3) -> list[str]:
    values = series.dropna().astype(str).str.strip()
    values = values[values != ""]
    return values.head(limit).tolist()


def _value_match_ratio(series: pd.Series, pattern: re.Pattern[str]) -> float:
    values = series.dropna().astype(str).str.strip()
    values = values[values != ""]
    if values.empty:
        return 0.0
    matches = values.map(lambda item: bool(pattern.match(item))).sum()
    return round(matches / len(values), 3)


def _datetime_ratio(series: pd.Series, column_name: str) -> float:
    values = series.dropna()
    if values.empty:
        return 0.0
    lowered = column_name.lower()
    has_time_hint = any(token in lowered for token in ["time", "date", "timestamp", "start", "end"])
    if pd.api.types.is_numeric_dtype(values) and not has_time_hint:
        return 0.0
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        parsed = pd.to_datetime(values, errors="coerce")
    return round(parsed.notna().mean(), 3)


def _name_hint(column_name: str) -> dict[str, str]:
    lowered = column_name.lower()
    for keyword, meaning in NAME_HINTS.items():
        if keyword in lowered:
            return meaning
    return {}


def classify_column(df: pd.DataFrame, column: str) -> dict[str, Any]:
    series = df[column]
    hint = _name_hint(column)
    semantic_type = hint.get("semantic_type", "unknown")
    category = hint.get("category", "unknown")
    role = hint.get("role", "attribute")

    phone_ratio = _value_match_ratio(series, PHONE_PATTERN)
    ip_ratio = _value_match_ratio(series, IPV4_PATTERN)
    imei_ratio = _value_match_ratio(series, IMEI_PATTERN)
    imsi_ratio = _value_match_ratio(series, IMSI_PATTERN)
    datetime_ratio = _datetime_ratio(series, column)
    is_numeric = pd.api.types.is_numeric_dtype(series)

    confidence = 0.45 if hint else 0.15

    if semantic_type in {"imei", "imsi"}:
        confidence = max(confidence, 0.95)
    elif datetime_ratio >= 0.7:
        semantic_type = "timestamp"
        category = "time"
        confidence = max(confidence, datetime_ratio)
    elif ip_ratio >= 0.7:
        semantic_type = "ip_address"
        category = "entity"
        confidence = max(confidence, ip_ratio)
    elif "imei" in column.lower() or imei_ratio >= 0.7:
        semantic_type = "imei"
        category = "entity"
        confidence = max(confidence, imei_ratio)
    elif "imsi" in column.lower() or imsi_ratio >= 0.7:
        semantic_type = "imsi"
        category = "entity"
        confidence = max(confidence, imsi_ratio)
    elif phone_ratio >= 0.7:
        semantic_type = "phone_number"
        category = "relationship" if role in {"source", "target"} else "entity"
        confidence = max(confidence, phone_ratio)
    elif "lat" in column.lower() and is_numeric:
        semantic_type = "latitude"
        category = "location"
        confidence = max(confidence, 0.9)
    elif ("lon" in column.lower() or "lng" in column.lower()) and is_numeric:
        semantic_type = "longitude"
        category = "location"
        confidence = max(confidence, 0.9)
    elif ("duration" in column.lower() or "bytes" in column.lower() or "upload" in column.lower() or "download" in column.lower()) and is_numeric:
        if "duration" in column.lower():
            semantic_type = "duration"
        elif "upload" in column.lower():
            semantic_type = "upload_volume"
        elif "download" in column.lower():
            semantic_type = "download_volume"
        else:
            semantic_type = "volume"
        category = "metric"
        confidence = max(confidence, 0.85)
    elif category == "unknown" and is_numeric:
        semantic_type = "numeric_metric"
        category = "metric"
        confidence = max(confidence, 0.4)

    return {
        "column": column,
        "dtype": str(series.dtype),
        "semantic_type": semantic_type,
        "category": category,
        "role": role,
        "confidence": round(float(confidence), 2),
        "non_null_count": int(series.notna().sum()),
        "unique_count": int(series.dropna().astype(str).str.strip().nunique()),
        "examples": _series_examples(series),
    }


def build_relationship_pairs(column_profiles: list[dict[str, Any]]) -> list[dict[str, str]]:
    source_columns = [item["column"] for item in column_profiles if item["role"] == "source"]
    target_columns = [item["column"] for item in column_profiles if item["role"] == "target"]
    pairs = [{"source": source, "target": target} for source in source_columns for target in target_columns if source != target]
    if pairs:
        return pairs[:3]

    entity_columns = [item["column"] for item in column_profiles if item["category"] in {"entity", "relationship"}]
    if len(entity_columns) >= 2:
        return [{"source": entity_columns[0], "target": entity_columns[1]}]
    return []


def summarize_dataset(file_name: str, df: pd.DataFrame) -> dict[str, Any]:
    column_profiles = [classify_column(df, column) for column in df.columns]
    stats: dict[str, Any] = {
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "missing_values": int(df.isna().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
    }

    category_map: dict[str, list[str]] = {}
    semantic_map: dict[str, list[str]] = {}
    for profile in column_profiles:
        category_map.setdefault(profile["category"], []).append(profile["column"])
        semantic_map.setdefault(profile["semantic_type"], []).append(profile["column"])

    preview_rows = df.head(3).fillna("").astype(str).to_dict(orient="records")
    dataset_type_guess = "generic_structured_data"
    semantic_types = semantic_map.keys()
    has_relationships = bool(build_relationship_pairs(column_profiles))
    if has_relationships and "duration" in semantic_types and "timestamp" in semantic_types:
        dataset_type_guess = "cdr"
    elif "tower_id" in semantic_types and "timestamp" in semantic_types:
        dataset_type_guess = "tower_dump"
    elif "ip_address" in semantic_types and "timestamp" in semantic_types:
        dataset_type_guess = "ipdr"

    return {
        "file_name": file_name,
        "rows": int(len(df)),
        "columns": df.columns.tolist(),
        "column_profiles": column_profiles,
        "semantic_summary": {
            "categories": category_map,
            "semantic_types": semantic_map,
            "relationship_pairs": build_relationship_pairs(column_profiles),
        },
        "entity_columns": category_map.get("entity", []) + category_map.get("relationship", []),
        "time_columns": category_map.get("time", []),
        "location_columns": category_map.get("location", []),
        "dataset_type_guess": dataset_type_guess,
        "stats": stats,
        "preview_rows": preview_rows,
    }
