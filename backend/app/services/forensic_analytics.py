from __future__ import annotations

from collections import Counter, defaultdict
from datetime import timedelta
from statistics import median
from typing import Any
import re

import pandas as pd

from app.services.datetime_utils import coerce_datetime


VPN_KEYWORDS = {"vpn", "nordvpn", "expressvpn", "protonvpn", "surfshark", "wireguard", "openvpn"}
TOR_KEYWORDS = {"tor", "onion", "tor2web", "torbrowser", "9050", "9051"}
ENCRYPTED_APP_KEYWORDS = {
    "whatsapp": "WhatsApp",
    "telegram": "Telegram",
    "signal": "Signal",
    "wickr": "Wickr",
    "session": "Session",
    "threema": "Threema",
}
SUSPICIOUS_IPS = {
    "185.220.101.45",
    "45.142.212.100",
    "193.32.127.80",
    "104.21.14.100",
}
SUSPICIOUS_HOST_KEYWORDS = {"bulletproof", "exit node", "dark web", "onion", "tor", "forum", "market"}
MONTH_MAP = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}


def _coerce_datetime(series: pd.Series) -> pd.Series:
    return coerce_datetime(series)


def _dataset_profiles(dataset: dict[str, Any]) -> list[dict[str, Any]]:
    return dataset["summary"].get("column_profiles", [])


def _profile_lookup(dataset: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {profile["column"]: profile for profile in _dataset_profiles(dataset)}


def _find_profiles(
    dataset: dict[str, Any],
    *,
    semantic_types: set[str] | None = None,
    categories: set[str] | None = None,
    role: str | None = None,
    name_keywords: tuple[str, ...] = (),
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for profile in _dataset_profiles(dataset):
        if semantic_types and profile.get("semantic_type") not in semantic_types:
            continue
        if categories and profile.get("category") not in categories:
            continue
        if role and profile.get("role") != role:
            continue
        if name_keywords and not any(keyword in profile["column"].lower() for keyword in name_keywords):
            continue
        results.append(profile)
    return results


def _find_first_profile(dataset: dict[str, Any], **kwargs: Any) -> dict[str, Any] | None:
    profiles = _find_profiles(dataset, **kwargs)
    return profiles[0] if profiles else None


def _find_time_column(dataset: dict[str, Any]) -> str | None:
    profile = _find_first_profile(dataset, semantic_types={"timestamp"}, categories={"time"})
    return profile["column"] if profile else None


def _clean_series(df: pd.DataFrame, column: str) -> pd.Series:
    values = df[column].fillna("").astype(str).str.strip()
    return values[values != ""]


def _is_cdr_dataset(dataset: dict[str, Any]) -> bool:
    if dataset["summary"].get("dataset_type_guess") == "cdr":
        return True
    return bool(_find_first_profile(dataset, role="source")) and bool(_find_first_profile(dataset, role="target"))


def _is_tower_dataset(dataset: dict[str, Any]) -> bool:
    if dataset["summary"].get("dataset_type_guess") == "tower_dump":
        return True
    return bool(_find_first_profile(dataset, semantic_types={"tower_id"}, categories={"location"})) and bool(
        _find_time_column(dataset)
    )


def _is_ipdr_dataset(dataset: dict[str, Any]) -> bool:
    if dataset["summary"].get("dataset_type_guess") == "ipdr":
        return True
    return bool(_find_first_profile(dataset, semantic_types={"ip_address"}, categories={"entity"})) and bool(
        _find_time_column(dataset)
    )


def _cdr_datasets(datasets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [dataset for dataset in datasets if _is_cdr_dataset(dataset)]


def _tower_datasets(datasets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [dataset for dataset in datasets if _is_tower_dataset(dataset)]


def _ipdr_datasets(datasets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [dataset for dataset in datasets if _is_ipdr_dataset(dataset)]


def _cdr_columns(dataset: dict[str, Any]) -> dict[str, str | None]:
    source = _find_first_profile(dataset, role="source")
    target = _find_first_profile(dataset, role="target")
    duration = _find_first_profile(dataset, semantic_types={"duration"}, categories={"metric"})
    time_column = _find_time_column(dataset)
    tower = _find_first_profile(dataset, semantic_types={"tower_id"}, categories={"location"})
    return {
        "source": source["column"] if source else None,
        "target": target["column"] if target else None,
        "duration": duration["column"] if duration else None,
        "time": time_column,
        "tower": tower["column"] if tower else None,
    }


def _tower_columns(dataset: dict[str, Any]) -> dict[str, str | None]:
    entity = _find_first_profile(dataset, semantic_types={"phone_number"}, categories={"entity", "relationship"})
    if not entity:
        entity = _find_first_profile(dataset, categories={"entity", "relationship"})
    tower = _find_first_profile(dataset, semantic_types={"tower_id"}, categories={"location"})
    city = _find_first_profile(dataset, semantic_types={"city"}, categories={"location"}, name_keywords=("city",))
    location = _find_first_profile(dataset, semantic_types={"location_label"}, categories={"location"})
    sector = _find_first_profile(dataset, name_keywords=("sector",), categories={"location"})
    time_column = _find_time_column(dataset)
    return {
        "entity": entity["column"] if entity else None,
        "tower": tower["column"] if tower else None,
        "city": city["column"] if city else None,
        "location": location["column"] if location else None,
        "sector": sector["column"] if sector else None,
        "time": time_column,
    }


def _ipdr_columns(dataset: dict[str, Any]) -> dict[str, str | None]:
    entity = _find_first_profile(dataset, semantic_types={"phone_number"}, categories={"entity", "relationship"}, name_keywords=("user", "subscriber", "msisdn", "number"))
    if not entity:
        entity = _find_first_profile(dataset, semantic_types={"phone_number"}, categories={"entity", "relationship"})
    ip_address = _find_first_profile(dataset, semantic_types={"ip_address"}, categories={"entity"})
    host = _find_first_profile(dataset, semantic_types={"domain"}, categories={"network"})
    app = _find_first_profile(dataset, semantic_types={"application"}, categories={"network"})
    upload = _find_first_profile(dataset, semantic_types={"upload_volume"}, categories={"metric"})
    download = _find_first_profile(dataset, semantic_types={"download_volume"}, categories={"metric"})
    volume = _find_first_profile(dataset, semantic_types={"volume"}, categories={"metric"})
    start = _find_first_profile(dataset, semantic_types={"timestamp"}, categories={"time"}, name_keywords=("start", "time", "date", "session"))
    end = _find_first_profile(dataset, semantic_types={"timestamp"}, categories={"time"}, name_keywords=("end",))
    device = _find_first_profile(dataset, semantic_types={"device_id", "imei", "imsi"}, categories={"entity"})
    port = _find_first_profile(dataset, semantic_types={"port"}, categories={"network"})
    return {
        "entity": entity["column"] if entity else None,
        "ip": ip_address["column"] if ip_address else None,
        "host": host["column"] if host else None,
        "app": app["column"] if app else None,
        "upload": upload["column"] if upload else None,
        "download": download["column"] if download else None,
        "volume": volume["column"] if volume else None,
        "start": start["column"] if start else _find_time_column(dataset),
        "end": end["column"] if end else None,
        "device": device["column"] if device else None,
        "port": port["column"] if port else None,
    }


def _extract_city_from_tower(value: Any) -> str | None:
    text = str(value).strip()
    if not text:
        return None
    if "-" in text:
        parts = text.split("-")
        if len(parts) >= 3 and len(parts[1]) in {3, 4}:
            return parts[1]
    return None


def _is_between_hours(hour: int, start_hour: int, end_hour: int) -> bool:
    if start_hour <= end_hour:
        return start_hour <= hour <= end_hour
    return hour >= start_hour or hour <= end_hour


def _format_timestamp(value: Any) -> str:
    if value is None or pd.isna(value):
        return "unknown time"
    ts = pd.Timestamp(value)
    return ts.strftime("%Y-%m-%d %H:%M")


def _format_date(value: Any) -> str:
    if value is None or pd.isna(value):
        return "unknown date"
    ts = pd.Timestamp(value)
    return ts.strftime("%Y-%m-%d")


def _duration_summary(values: list[float]) -> str:
    if not values:
        return "No duration data"
    avg_value = round(sum(values) / len(values), 1)
    return f"Average duration: {avg_value} seconds"


def _response_override(
    title: str,
    direct_answer: str,
    supporting_data: list[str],
    analysis: str,
    insight: str,
    recommended_action: str,
    focus_entity: str | None = None,
    suggestions: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "title": title,
        "direct_answer": direct_answer,
        "supporting_data": supporting_data,
        "analysis": analysis,
        "insight": insight,
        "recommended_action": recommended_action,
        "focus_entity": focus_entity,
        "suggestions": suggestions or [],
    }


def parse_date_window(query_text: str) -> dict[str, int | None] | None:
    normalized = query_text.lower().replace("–", "-")
    month_pattern = re.search(r"(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:t|tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+(\d{1,2})(?:\s*-\s*(\d{1,2}))?(?:,\s*(\d{4}))?", normalized)
    if not month_pattern:
        return None
    month = MONTH_MAP[month_pattern.group(1)]
    start_day = int(month_pattern.group(2))
    end_day = int(month_pattern.group(3) or month_pattern.group(2))
    year = int(month_pattern.group(4)) if month_pattern.group(4) else None
    return {"month": month, "start_day": start_day, "end_day": end_day, "year": year}


def _filter_by_date_window(df: pd.DataFrame, time_column: str, date_window: dict[str, int | None] | None) -> pd.DataFrame:
    if not date_window:
        return df
    working = df.copy()
    working["_ts_filter"] = _coerce_datetime(working[time_column])
    working = working.dropna(subset=["_ts_filter"])
    if working.empty:
        return working
    month = date_window["month"]
    start_day = date_window["start_day"]
    end_day = date_window["end_day"]
    year = date_window.get("year")
    mask = (working["_ts_filter"].dt.month == month) & (working["_ts_filter"].dt.day >= start_day) & (working["_ts_filter"].dt.day <= end_day)
    if year:
        mask = mask & (working["_ts_filter"].dt.year == year)
    return working[mask]


def analyze_cdr_outgoing_callers(datasets: list[dict[str, Any]], limit: int = 5) -> dict[str, Any]:
    caller_counter: Counter[str] = Counter()
    datasets_used: list[str] = []

    for dataset in _cdr_datasets(datasets):
        columns = _cdr_columns(dataset)
        source = columns["source"]
        if not source:
            continue
        caller_counter.update(_clean_series(dataset["dataframe"], source).tolist())
        datasets_used.append(dataset["file_name"])

    ranking = [{"value": value, "count": count} for value, count in caller_counter.most_common(limit)]
    top = ranking[0] if ranking else None
    leads = [f"{top['value']} has the highest outgoing call count in the CDR data." ] if top else []
    return {
        "top_callers": ranking,
        "datasets_used": datasets_used,
        "leads": leads,
        "alerts": [],
        "visualizations": {"frequency_chart": [{"label": item["value"], "value": item["count"]} for item in ranking]},
        "response_override": _response_override(
            title=f"Top Caller: {top['value']}" if top else "CDR Call Frequency",
            direct_answer=f"{top['value']} made {top['count']} outgoing calls." if top else "No outgoing call records were found.",
            supporting_data=[f"{item['value']}: {item['count']} outgoing calls" for item in ranking],
            analysis=(
                f"{top['value']} leads the CDR caller ranking by {top['count'] - ranking[1]['count']} calls over {ranking[1]['value']}."
                if top and len(ranking) > 1
                else "The caller ranking is based only on source-side CDR records."
            ),
            insight=f"{top['value']} is the primary outgoing call driver in the available CDR data." if top else "Upload a CDR dataset with caller records to run this analysis.",
            recommended_action="Review the top caller's contacts, time pattern, and cross-dataset presence.",
            focus_entity=top["value"] if top else None,
            suggestions=["Who called that number?", "Show night calls", "Show calls between two numbers"],
        ),
    }


def analyze_cdr_incoming_receivers(datasets: list[dict[str, Any]], limit: int = 5) -> dict[str, Any]:
    receiver_counter: Counter[str] = Counter()
    datasets_used: list[str] = []

    for dataset in _cdr_datasets(datasets):
        columns = _cdr_columns(dataset)
        target = columns["target"]
        if not target:
            continue
        receiver_counter.update(_clean_series(dataset["dataframe"], target).tolist())
        datasets_used.append(dataset["file_name"])

    ranking = [{"value": value, "count": count} for value, count in receiver_counter.most_common(limit)]
    top = ranking[0] if ranking else None
    return {
        "top_receivers": ranking,
        "datasets_used": datasets_used,
        "leads": [],
        "alerts": [],
        "visualizations": {"frequency_chart": [{"label": item["value"], "value": item["count"]} for item in ranking]},
        "response_override": _response_override(
            title=f"Top Receiver: {top['value']}" if top else "Incoming Call Ranking",
            direct_answer=f"{top['value']} received {top['count']} calls." if top else "No receiver-side call records were found.",
            supporting_data=[f"{item['value']}: {item['count']} received calls" for item in ranking],
            analysis="The ranking is based only on receiver-side CDR matches.",
            insight=f"{top['value']} is the most contacted target in the CDR data." if top else "Upload a CDR dataset with receiver records to run this analysis.",
            recommended_action="Check who called the top receiver and whether those calls cluster by date or hour.",
            focus_entity=top["value"] if top else None,
        ),
    }


def analyze_cdr_calls_to_entity(datasets: list[dict[str, Any]], entity: str) -> dict[str, Any]:
    caller_counter: Counter[str] = Counter()
    events: list[dict[str, Any]] = []
    duration_values: list[float] = []
    night_hits = 0
    datasets_used: list[str] = []

    for dataset in _cdr_datasets(datasets):
        columns = _cdr_columns(dataset)
        source, target, time_column, duration_column = columns["source"], columns["target"], columns["time"], columns["duration"]
        if not source or not target:
            continue
        subset = dataset["dataframe"][[source, target] + [column for column in [time_column, duration_column] if column]].dropna(subset=[source, target]).copy()
        subset[source] = subset[source].astype(str).str.strip()
        subset[target] = subset[target].astype(str).str.strip()
        subset = subset[subset[target] == entity]
        if subset.empty:
            continue
        datasets_used.append(dataset["file_name"])
        caller_counter.update(subset[source].tolist())
        if time_column:
            subset["_ts"] = _coerce_datetime(subset[time_column])
        else:
            subset["_ts"] = pd.NaT
        if duration_column:
            subset["_duration"] = pd.to_numeric(subset[duration_column], errors="coerce")
        else:
            subset["_duration"] = pd.NA
        for _, row in subset.iterrows():
            if pd.notna(row["_ts"]) and _is_between_hours(int(row["_ts"].hour), 21, 23):
                night_hits += 1
            if pd.notna(row["_duration"]):
                duration_values.append(float(row["_duration"]))
            events.append(
                {
                    "caller": row[source],
                    "receiver": row[target],
                    "timestamp": row["_ts"],
                    "duration": None if pd.isna(row["_duration"]) else float(row["_duration"]),
                    "file_name": dataset["file_name"],
                }
            )

    events.sort(key=lambda item: item["timestamp"] if item["timestamp"] is not None else pd.Timestamp.min)
    ranking = [{"value": value, "count": count} for value, count in caller_counter.most_common(5)]
    top = ranking[0] if ranking else None
    short_calls = len([value for value in duration_values if value <= 60])
    supporting = [f"{item['value']}: {item['count']} calls to {entity}" for item in ranking]
    supporting.extend(
        [f"{_format_timestamp(event['timestamp'])}: {event['caller']} -> {event['receiver']} ({int(event['duration']) if event['duration'] is not None else 'no'} sec)" for event in events[:3]]
    )
    leads = [f"{top['value']} is the top caller to {entity} with {top['count']} calls."] if top else []
    alerts = [f"{short_calls} calls to {entity} are short-duration calls (60 seconds or less)."] if short_calls >= 3 else []
    return {
        "entity": entity,
        "caller_ranking": ranking,
        "call_events": events[:25],
        "datasets_used": datasets_used,
        "leads": leads,
        "alerts": alerts,
        "visualizations": {"relationship_table": ranking},
        "response_override": _response_override(
            title=f"Calls To {entity}",
            direct_answer=f"{top['value']} called {entity} {top['count']} times." if top else f"No callers to {entity} were found in the CDR data.",
            supporting_data=supporting[:6],
            analysis=(
                f"{short_calls} of the matched calls are short-duration calls. {_duration_summary(duration_values)}."
                if events
                else "No CDR rows matched the requested receiver."
            ),
            insight=(
                f"{entity} receives repeated contact from {top['value']} in the matched period."
                if top
                else f"{entity} is not present as a receiver in the loaded CDR data."
            ),
            recommended_action=f"Compare the call dates for {entity} with tower and IPDR activity in the same window.",
            focus_entity=entity,
            suggestions=["Who called that number most?", "Show calls between two numbers", "Show their night activity"],
        ),
    }


def analyze_cdr_night_calls(datasets: list[dict[str, Any]], start_hour: int = 22, end_hour: int = 6) -> dict[str, Any]:
    actor_counter: Counter[str] = Counter()
    pair_counter: Counter[tuple[str, str]] = Counter()
    events: list[dict[str, Any]] = []
    datasets_used: list[str] = []

    for dataset in _cdr_datasets(datasets):
        columns = _cdr_columns(dataset)
        source, target, time_column, duration_column = columns["source"], columns["target"], columns["time"], columns["duration"]
        if not source or not target or not time_column:
            continue
        subset = dataset["dataframe"][[source, target, time_column] + ([duration_column] if duration_column else [])].copy()
        subset["_ts"] = _coerce_datetime(subset[time_column])
        subset = subset.dropna(subset=["_ts", source, target])
        if subset.empty:
            continue
        subset[source] = subset[source].astype(str).str.strip()
        subset[target] = subset[target].astype(str).str.strip()
        subset = subset[subset["_ts"].dt.hour.map(lambda hour: _is_between_hours(int(hour), start_hour, end_hour))]
        if subset.empty:
            continue
        datasets_used.append(dataset["file_name"])
        for _, row in subset.iterrows():
            actor_counter.update([row[source], row[target]])
            pair_counter.update([(row[source], row[target])])
            events.append(
                {
                    "source": row[source],
                    "target": row[target],
                    "timestamp": row["_ts"],
                    "duration": None if not duration_column else pd.to_numeric(row[duration_column], errors="coerce"),
                    "file_name": dataset["file_name"],
                }
            )

    events.sort(key=lambda item: item["timestamp"])
    top_actors = [{"value": value, "count": count} for value, count in actor_counter.most_common(5)]
    top_pairs = [{"source": pair[0], "target": pair[1], "count": count} for pair, count in pair_counter.most_common(5)]
    alerts = [f"{item['source']} -> {item['target']} appears {item['count']} times during night hours." for item in top_pairs[:3] if item["count"] >= 2]
    return {
        "night_call_events": events[:50],
        "top_actors": top_actors,
        "top_pairs": top_pairs,
        "datasets_used": datasets_used,
        "leads": [f"{top_actors[0]['value']} is the most visible actor in night calls."] if top_actors else [],
        "alerts": alerts[:5],
        "visualizations": {"relationship_table": [{"label": item["value"], "value": item["count"]} for item in top_actors]},
        "response_override": _response_override(
            title="Night Call Activity",
            direct_answer=f"{len(events)} calls were made between {start_hour:02d}:00 and {end_hour:02d}:00." if events else "No night-time CDR calls were found.",
            supporting_data=[f"{item['value']}: {item['count']} night-call appearances" for item in top_actors[:5]],
            analysis=(
                "The night-call set is ranked by entity appearances in matched late-hour call records."
                if events
                else "The CDR data contains no call records inside the requested night window."
            ),
            insight=(
                f"{top_actors[0]['value']} is the key actor in the matched night-time communication set."
                if top_actors
                else "There is no late-hour call cluster in the available CDR data."
            ),
            recommended_action="Check the strongest night-call pair against tower co-location and IPDR activity in the same time window.",
            suggestions=["Show top callers", "Show calls between two numbers", "Find suspicious activity"],
        ),
    }


def analyze_cdr_pair_history(
    datasets: list[dict[str, Any]],
    entity_a: str,
    entity_b: str,
    *,
    night_only: bool = False,
    start_hour: int = 22,
    end_hour: int = 6,
) -> dict[str, Any]:
    return analyze_cdr_pair_history_filtered(
        datasets,
        entity_a,
        entity_b,
        night_only=night_only,
        start_hour=start_hour,
        end_hour=end_hour,
    )


def analyze_cdr_pair_history_filtered(
    datasets: list[dict[str, Any]],
    entity_a: str,
    entity_b: str,
    *,
    night_only: bool = False,
    start_hour: int = 22,
    end_hour: int = 6,
) -> dict[str, Any]:
    events: list[dict[str, Any]] = []
    duration_values: list[float] = []
    direction_counter: Counter[str] = Counter()
    daily_counter: Counter[str] = Counter()
    hour_counter: Counter[int] = Counter()
    datasets_used: list[str] = []

    for dataset in _cdr_datasets(datasets):
        columns = _cdr_columns(dataset)
        source, target, time_column, duration_column = columns["source"], columns["target"], columns["time"], columns["duration"]
        if not source or not target:
            continue
        subset = dataset["dataframe"][[source, target] + [column for column in [time_column, duration_column] if column]].dropna(subset=[source, target]).copy()
        subset[source] = subset[source].astype(str).str.strip()
        subset[target] = subset[target].astype(str).str.strip()
        subset = subset[
            ((subset[source] == entity_a) & (subset[target] == entity_b))
            | ((subset[source] == entity_b) & (subset[target] == entity_a))
        ]
        if subset.empty:
            continue
        datasets_used.append(dataset["file_name"])
        subset["_ts"] = _coerce_datetime(subset[time_column]) if time_column else pd.NaT
        subset = subset.dropna(subset=["_ts"]) if time_column else subset
        if night_only and time_column:
            subset = subset[subset["_ts"].dt.hour.map(lambda hour: _is_between_hours(int(hour), start_hour, end_hour))]
        if subset.empty:
            continue
        subset["_duration"] = pd.to_numeric(subset[duration_column], errors="coerce") if duration_column else pd.NA
        for _, row in subset.iterrows():
            if pd.notna(row["_duration"]):
                duration_values.append(float(row["_duration"]))
            direction_counter.update([f"{row[source]} -> {row[target]}"])
            if pd.notna(row["_ts"]):
                daily_counter.update([_format_date(row["_ts"])])
                hour_counter.update([int(row["_ts"].hour)])
            events.append(
                {
                    "source": row[source],
                    "target": row[target],
                    "timestamp": row["_ts"],
                    "duration": None if pd.isna(row["_duration"]) else float(row["_duration"]),
                    "file_name": dataset["file_name"],
                }
            )

    events.sort(key=lambda item: item["timestamp"] if item["timestamp"] is not None else pd.Timestamp.min)
    if not events:
        return {
            "pair_history": [],
            "datasets_used": [],
            "leads": [],
            "alerts": [],
            "visualizations": {"relationship_table": []},
            "response_override": _response_override(
                title=f"No Pair History: {entity_a} and {entity_b}",
                direct_answer=(
                    f"No direct night-time CDR calls were found between {entity_a} and {entity_b}."
                    if night_only
                    else f"No direct CDR calls were found between {entity_a} and {entity_b}."
                ),
                supporting_data=[],
                analysis=(
                    "The pair filter did not match any source-target or target-source rows inside the requested night window."
                    if night_only
                    else "The pair filter did not match any source-target or target-source rows in the loaded CDR data."
                ),
                insight=(
                    "The two entities do not appear as a direct night-time call pair in the available data."
                    if night_only
                    else "The two entities do not appear as a direct call pair in the available data."
                ),
                recommended_action="Confirm both numbers and retry, or inspect each number separately.",
            ),
        }

    top_direction = direction_counter.most_common(1)[0]
    top_hours = sorted(hour_counter.items(), key=lambda item: item[1], reverse=True)[:2]
    analysis_text = f"{len(events)} calls were found between the pair. {top_direction[0]} is the dominant direction with {top_direction[1]} calls."
    if top_hours:
        analysis_text += " Peak hours: " + ", ".join(f"{hour:02d}:00 ({count})" for hour, count in top_hours) + "."
    insight_text = f"The pair shows repeated contact across {len(daily_counter)} distinct day(s)."
    distinct_dates = sorted(pd.to_datetime(list(daily_counter.keys()), errors="coerce").dropna().tolist())
    consecutive_span = False
    if distinct_dates:
        min_date = min(distinct_dates)
        max_date = max(distinct_dates)
        consecutive_span = (max_date - min_date).days + 1 == len(distinct_dates)
    alerts: list[str] = []
    if consecutive_span and len(daily_counter) >= 5:
        alerts.append(f"{entity_a} and {entity_b} have contact on {len(daily_counter)} consecutive day(s).")
    elif len(events) >= 10:
        alerts.append(f"{entity_a} and {entity_b} have repeated direct contact.")
    return {
        "pair_history": events[:50],
        "direction_counts": [{"direction": key, "count": value} for key, value in direction_counter.items()],
        "daily_counts": [{"date": key, "count": value} for key, value in daily_counter.items()],
        "datasets_used": datasets_used,
        "leads": [f"{entity_a} and {entity_b} are a repeated call pair with {len(events)} matched records."],
        "alerts": alerts,
        "visualizations": {"relationship_table": [{"label": key, "value": value} for key, value in direction_counter.items()]},
        "response_override": _response_override(
            title=f"{'Night ' if night_only else ''}Pair History: {entity_a} and {entity_b}",
            direct_answer=(
                f"{entity_a} and {entity_b} have {len(events)} direct night-time call records."
                if night_only
                else f"{entity_a} and {entity_b} have {len(events)} direct call records."
            ),
            supporting_data=[
                f"Dominant direction: {top_direction[0]} ({top_direction[1]} calls)",
                _duration_summary(duration_values),
                f"Distinct days: {len(daily_counter)}",
            ],
            analysis=analysis_text,
            insight=insight_text,
            recommended_action="Review the exact call dates, duration spikes, and same-day tower activity for both numbers.",
            focus_entity=entity_a,
            suggestions=["Show day-by-day pattern", "Show their tower co-location", "Build complete profile"],
        ),
    }


def trace_ip_activity_across_datasets(datasets: list[dict[str, Any]], limit: int = 5) -> dict[str, Any]:
    sessions = _extract_ipdr_rows(datasets)
    if not sessions:
        return {
            "ip_activity_ranking": [],
            "datasets_used": [],
            "leads": [],
            "alerts": [],
            "visualizations": {"relationship_table": []},
            "response_override": _response_override(
                title="Cross-Dataset IP Activity",
                direct_answer="No IPDR activity was found in the loaded case data.",
                supporting_data=[],
                analysis="This query needs IPDR data with subscriber or device activity tied to IP records.",
                insight="Upload IPDR data to trace internet activity across the case datasets.",
                recommended_action="Add IPDR files or ask about phone-number or call analysis instead.",
            ),
        }

    entity_summary: dict[str, dict[str, Any]] = defaultdict(lambda: {"session_count": 0, "ip_values": set(), "ipdr_files": set()})
    common_entities = find_common_entities_bridge(datasets).get("common_entities", [])
    common_lookup = {item["value"]: item for item in common_entities}

    for row in sessions:
        bucket = entity_summary[row["entity"]]
        bucket["session_count"] += 1
        if row["ip_address"]:
            bucket["ip_values"].add(row["ip_address"])
        bucket["ipdr_files"].add(row["file_name"])

    ranking: list[dict[str, Any]] = []
    for entity, stats in entity_summary.items():
        file_count = common_lookup.get(entity, {}).get("file_count", len(stats["ipdr_files"]))
        ranking.append(
            {
                "value": entity,
                "session_count": int(stats["session_count"]),
                "distinct_ips": len(stats["ip_values"]),
                "file_count": int(file_count),
            }
        )

    ranking.sort(key=lambda item: (-item["file_count"], -item["session_count"], -item["distinct_ips"], item["value"]))
    top = ranking[0] if ranking else None
    return {
        "ip_activity_ranking": ranking[:limit],
        "datasets_used": sorted({row["file_name"] for row in sessions}),
        "leads": [f"{top['value']} has the strongest combined IP activity and cross-dataset presence."] if top else [],
        "alerts": [],
        "visualizations": {"relationship_table": [{"label": item["value"], "value": item["session_count"]} for item in ranking[:limit]]},
        "response_override": _response_override(
            title=f"Cross-Dataset IP Activity: {top['value']}" if top else "Cross-Dataset IP Activity",
            direct_answer=(
                f"{top['value']} has {top['session_count']} IPDR session(s), {top['distinct_ips']} distinct IPs, and appears in {top['file_count']} dataset(s)."
                if top
                else "No IP activity could be ranked."
            ),
            supporting_data=[
                f"{item['value']}: {item['session_count']} IPDR session(s), {item['distinct_ips']} IPs, {item['file_count']} dataset(s)"
                for item in ranking[:limit]
            ],
            analysis="The ranking combines IPDR session count, distinct IP values, and cross-dataset presence for the same entity.",
            insight=f"{top['value']} is the strongest IP-activity anchor across the loaded datasets." if top else "The loaded data does not support cross-dataset IP tracing yet.",
            recommended_action="Open the top entity profile and compare IP activity with calls and tower movement in the same period.",
            focus_entity=top["value"] if top else None,
            suggestions=["Build complete profile", "Show suspicious IPs", "Show their night activity"],
        ),
    }


def analyze_cdr_day_week_patterns(datasets: list[dict[str, Any]], entity: str | None = None, pair: tuple[str, str] | None = None) -> dict[str, Any]:
    day_counter: Counter[str] = Counter()
    weekday_counter: Counter[str] = Counter()
    datasets_used: list[str] = []
    total_records = 0

    for dataset in _cdr_datasets(datasets):
        columns = _cdr_columns(dataset)
        source, target, time_column = columns["source"], columns["target"], columns["time"]
        if not source or not target or not time_column:
            continue
        subset = dataset["dataframe"][[source, target, time_column]].copy()
        subset["_ts"] = _coerce_datetime(subset[time_column])
        subset = subset.dropna(subset=["_ts", source, target])
        subset[source] = subset[source].astype(str).str.strip()
        subset[target] = subset[target].astype(str).str.strip()
        if pair:
            a_value, b_value = pair
            subset = subset[
                ((subset[source] == a_value) & (subset[target] == b_value))
                | ((subset[source] == b_value) & (subset[target] == a_value))
            ]
        elif entity:
            subset = subset[(subset[source] == entity) | (subset[target] == entity)]
        if subset.empty:
            continue
        datasets_used.append(dataset["file_name"])
        total_records += len(subset)
        day_counter.update(subset["_ts"].dt.strftime("%Y-%m-%d").tolist())
        weekday_counter.update(subset["_ts"].dt.day_name().tolist())

    supporting = [f"{date}: {count} records" for date, count in day_counter.most_common(5)]
    supporting.extend([f"{day}: {count} records" for day, count in weekday_counter.most_common(3)])
    subject = f"{pair[0]} and {pair[1]}" if pair else entity or "the selected call set"
    return {
        "daily_counts": [{"date": date, "count": count} for date, count in day_counter.items()],
        "weekday_counts": [{"weekday": day, "count": count} for day, count in weekday_counter.items()],
        "datasets_used": datasets_used,
        "leads": [f"{subject} has a measurable day-by-day call pattern."] if total_records else [],
        "alerts": [],
        "visualizations": {"time_chart": [{"bucket": date, "value": count} for date, count in day_counter.items()]},
        "response_override": _response_override(
            title=f"Day and Week Pattern: {subject}",
            direct_answer=f"{total_records} CDR records were mapped for {subject}." if total_records else f"No dated CDR records were found for {subject}.",
            supporting_data=supporting[:8],
            analysis="The pattern is based on per-day and per-weekday counts from matched CDR timestamps.",
            insight=f"{subject} shows repeated activity on the highest-count dates and weekdays." if total_records else "There is no usable timestamp pattern for the requested subject.",
            recommended_action="Compare the busiest dates with tower and IPDR events from the same period.",
            focus_entity=entity,
        ),
    }


def profile_burner_cdr_entity(datasets: list[dict[str, Any]], entity: str) -> dict[str, Any]:
    contact_counter: Counter[str] = Counter()
    events: list[dict[str, Any]] = []
    night_hits = 0
    duration_values: list[float] = []
    datasets_used: list[str] = []

    for dataset in _cdr_datasets(datasets):
        columns = _cdr_columns(dataset)
        source, target, time_column, duration_column = columns["source"], columns["target"], columns["time"], columns["duration"]
        if not source or not target or not time_column:
            continue
        subset = dataset["dataframe"][[source, target, time_column] + ([duration_column] if duration_column else [])].copy()
        subset["_ts"] = _coerce_datetime(subset[time_column])
        subset = subset.dropna(subset=["_ts", source, target])
        subset[source] = subset[source].astype(str).str.strip()
        subset[target] = subset[target].astype(str).str.strip()
        subset = subset[(subset[source] == entity) | (subset[target] == entity)]
        if subset.empty:
            continue
        datasets_used.append(dataset["file_name"])
        for _, row in subset.iterrows():
            counterpart = row[target] if row[source] == entity else row[source]
            contact_counter.update([counterpart])
            if _is_between_hours(int(row["_ts"].hour), 22, 6):
                night_hits += 1
            duration_value = pd.to_numeric(row[duration_column], errors="coerce") if duration_column else pd.NA
            if pd.notna(duration_value):
                duration_values.append(float(duration_value))
            events.append(
                {
                    "timestamp": row["_ts"],
                    "counterpart": counterpart,
                    "duration": None if pd.isna(duration_value) else float(duration_value),
                    "direction": "outgoing" if row[source] == entity else "incoming",
                }
            )

    events.sort(key=lambda item: item["timestamp"])
    active_dates = [event["timestamp"].date() for event in events]
    active_days = len(set(active_dates))
    active_window = (min(active_dates), max(active_dates)) if active_dates else (None, None)
    top_contact = contact_counter.most_common(1)[0] if contact_counter else None
    alerts: list[str] = []
    if active_days and active_days <= 7:
        alerts.append(f"{entity} is active in a short window of {active_days} day(s).")
    if events and night_hits == len(events):
        alerts.append(f"{entity} operates only during night hours in the matched CDR records.")
    return {
        "entity": entity,
        "event_count": len(events),
        "active_days": active_days,
        "active_window": active_window,
        "top_contacts": [{"value": value, "count": count} for value, count in contact_counter.most_common(5)],
        "datasets_used": datasets_used,
        "leads": [f"{entity} interacts with {len(contact_counter)} unique contact(s)."] if events else [],
        "alerts": alerts,
        "visualizations": {"relationship_table": [{"label": value, "value": count} for value, count in contact_counter.most_common(5)]},
        "response_override": _response_override(
            title=f"Burner CDR Profile: {entity}",
            direct_answer=f"{entity} appears in {len(events)} CDR records across {active_days} active day(s)." if events else f"No CDR activity was found for {entity}.",
            supporting_data=[
                f"Active window: {_format_date(active_window[0]) if active_window[0] else 'unknown'} to {_format_date(active_window[1]) if active_window[1] else 'unknown'}",
                f"Night records: {night_hits}",
                _duration_summary(duration_values),
            ] + [f"{item['value']}: {item['count']} interactions" for item in [{"value": value, "count": count} for value, count in contact_counter.most_common(4)]],
            analysis=(
                f"{entity} has a short active window with {len(contact_counter)} unique contact(s)."
                if events
                else "The selected burner candidate does not appear in the loaded CDR data."
            ),
            insight=(
                f"{entity} shows a compact operational footprint in the CDR records."
                if events
                else f"{entity} has no usable CDR footprint in this case."
            ),
            recommended_action="Cross-check the candidate with tower co-location and flagged IPDR activity in the same window.",
            focus_entity=entity,
        ),
    }


def analyze_tower_top_hits(datasets: list[dict[str, Any]], limit: int = 5) -> dict[str, Any]:
    tower_counter: Counter[str] = Counter()
    datasets_used: list[str] = []

    for dataset in _tower_datasets(datasets):
        columns = _tower_columns(dataset)
        tower = columns["tower"]
        if not tower:
            continue
        tower_counter.update(_clean_series(dataset["dataframe"], tower).tolist())
        datasets_used.append(dataset["file_name"])

    ranking = [{"value": value, "count": count} for value, count in tower_counter.most_common(limit)]
    top = ranking[0] if ranking else None
    return {
        "tower_ranking": ranking,
        "datasets_used": datasets_used,
        "leads": [f"{top['value']} is the highest-hit tower in the loaded tower data."] if top else [],
        "alerts": [],
        "visualizations": {"frequency_chart": [{"label": item["value"], "value": item["count"]} for item in ranking]},
        "response_override": _response_override(
            title=f"Top Tower: {top['value']}" if top else "Tower Hit Ranking",
            direct_answer=f"{top['value']} has {top['count']} tower hits." if top else "No tower-hit data was found.",
            supporting_data=[f"{item['value']}: {item['count']} hits" for item in ranking],
            analysis="The ranking counts raw tower registrations across the loaded tower datasets.",
            insight=f"{top['value']} is the strongest location hub in the current tower data." if top else "Upload a tower dump dataset to run this analysis.",
            recommended_action="Check which entities appear most often at the top tower and whether they co-locate there.",
        ),
    }


def analyze_tower_colocation(datasets: list[dict[str, Any]], entity_a: str, entity_b: str, window_minutes: int = 30) -> dict[str, Any]:
    events: list[dict[str, Any]] = []
    datasets_used: list[str] = []

    for dataset in _tower_datasets(datasets):
        columns = _tower_columns(dataset)
        entity_column, tower_column, time_column = columns["entity"], columns["tower"], columns["time"]
        if not entity_column or not tower_column or not time_column:
            continue
        subset = dataset["dataframe"][[entity_column, tower_column, time_column]].copy()
        subset["_ts"] = _coerce_datetime(subset[time_column])
        subset = subset.dropna(subset=["_ts", entity_column, tower_column])
        subset[entity_column] = subset[entity_column].astype(str).str.strip()
        subset[tower_column] = subset[tower_column].astype(str).str.strip()
        subset_a = subset[subset[entity_column] == entity_a]
        subset_b = subset[subset[entity_column] == entity_b]
        if subset_a.empty or subset_b.empty:
            continue
        datasets_used.append(dataset["file_name"])
        for _, row_a in subset_a.iterrows():
            same_tower = subset_b[subset_b[tower_column] == row_a[tower_column]]
            if same_tower.empty:
                continue
            same_tower = same_tower.assign(_delta=(same_tower["_ts"] - row_a["_ts"]).abs())
            same_tower = same_tower[same_tower["_delta"] <= timedelta(minutes=window_minutes)]
            for _, row_b in same_tower.iterrows():
                events.append(
                    {
                        "tower": row_a[tower_column],
                        "timestamp_a": row_a["_ts"],
                        "timestamp_b": row_b["_ts"],
                        "gap_minutes": round(abs((row_b["_ts"] - row_a["_ts"]).total_seconds()) / 60, 1),
                        "file_name": dataset["file_name"],
                    }
                )

    events.sort(key=lambda item: (item["timestamp_a"], item["gap_minutes"]))
    return {
        "colocation_events": events[:30],
        "datasets_used": datasets_used,
        "leads": [f"{len(events)} co-location event(s) were found between {entity_a} and {entity_b}."] if events else [],
        "alerts": [f"{entity_a} and {entity_b} were at the same tower within {window_minutes} minutes."] if events else [],
        "visualizations": {"relationship_table": [{"label": event["tower"], "value": 1} for event in events[:10]]},
        "response_override": _response_override(
            title=f"Tower Co-Location: {entity_a} and {entity_b}",
            direct_answer=f"{len(events)} co-location event(s) were found within {window_minutes} minutes." if events else f"No co-location events were found between {entity_a} and {entity_b}.",
            supporting_data=[
                f"{event['tower']} at {_format_timestamp(event['timestamp_a'])} / {_format_timestamp(event['timestamp_b'])} ({event['gap_minutes']} min gap)"
                for event in events[:5]
            ],
            analysis=(
                "Events are counted when both entities hit the same tower within the configured time window."
                if events
                else "No same-tower events fell inside the configured co-location window."
            ),
            insight=f"{entity_a} and {entity_b} share physical proximity indicators in the tower data." if events else "The loaded tower data does not show physical proximity between the pair.",
            recommended_action="Cross-check the co-location times with calls and internet sessions from the same window.",
            focus_entity=entity_a,
        ),
    }


def analyze_tower_movement(datasets: list[dict[str, Any]], entity: str) -> dict[str, Any]:
    events: list[dict[str, Any]] = []
    datasets_used: list[str] = []

    for dataset in _tower_datasets(datasets):
        columns = _tower_columns(dataset)
        entity_column, tower_column, time_column = columns["entity"], columns["tower"], columns["time"]
        if not entity_column or not tower_column or not time_column:
            continue
        subset = dataset["dataframe"][[entity_column, tower_column, time_column] + [column for column in [columns["city"], columns["location"], columns["sector"]] if column]].copy()
        subset["_ts"] = _coerce_datetime(subset[time_column])
        subset = subset.dropna(subset=["_ts", entity_column, tower_column])
        subset[entity_column] = subset[entity_column].astype(str).str.strip()
        subset = subset[subset[entity_column] == entity]
        if subset.empty:
            continue
        datasets_used.append(dataset["file_name"])
        for _, row in subset.iterrows():
            city_value = row[columns["city"]] if columns["city"] and columns["city"] in row else None
            if not city_value and columns["tower"]:
                city_value = _extract_city_from_tower(row[tower_column])
            events.append(
                {
                    "timestamp": row["_ts"],
                    "tower": str(row[tower_column]),
                    "city": None if city_value is None or pd.isna(city_value) else str(city_value),
                    "file_name": dataset["file_name"],
                }
            )

    events.sort(key=lambda item: item["timestamp"])
    distinct_towers = sorted({event["tower"] for event in events})
    distinct_cities = sorted({event["city"] for event in events if event["city"]})
    path = []
    previous_tower = None
    for event in events:
        if event["tower"] != previous_tower:
            path.append(event)
            previous_tower = event["tower"]

    return {
        "movement_path": path[:30],
        "distinct_towers": distinct_towers,
        "distinct_cities": distinct_cities,
        "datasets_used": datasets_used,
        "leads": [f"{entity} appears across {len(distinct_towers)} tower(s)."] if events else [],
        "alerts": [f"{entity} appears across {len(distinct_cities)} distinct city marker(s)."] if len(distinct_cities) > 1 else [],
        "visualizations": {"relationship_table": [{"label": tower, "value": 1} for tower in distinct_towers[:10]]},
        "response_override": _response_override(
            title=f"Movement Reconstruction: {entity}",
            direct_answer=f"{entity} appears across {len(distinct_towers)} tower(s) and {len(distinct_cities)} distinct city marker(s)." if events else f"No tower movement data was found for {entity}.",
            supporting_data=[f"{_format_timestamp(event['timestamp'])}: {event['tower']}{' / ' + event['city'] if event['city'] else ''}" for event in path[:6]],
            analysis="The path is built from chronologically ordered tower registrations for the selected entity.",
            insight=f"{entity} has a measurable physical movement footprint in the tower data." if events else f"{entity} does not appear in the loaded tower datasets.",
            recommended_action="Compare the movement path with the entity's call pattern and suspicious internet sessions.",
            focus_entity=entity,
        ),
    }


def analyze_tower_spread(datasets: list[dict[str, Any]], limit: int = 5) -> dict[str, Any]:
    spread_rows: list[dict[str, Any]] = []

    for dataset in _tower_datasets(datasets):
        columns = _tower_columns(dataset)
        entity_column, tower_column = columns["entity"], columns["tower"]
        time_column = columns["time"]
        if not entity_column or not tower_column:
            continue
        subset = dataset["dataframe"][[entity_column, tower_column] + [column for column in [columns["city"], time_column] if column]].dropna(subset=[entity_column, tower_column]).copy()
        subset[entity_column] = subset[entity_column].astype(str).str.strip()
        grouped = subset.groupby(entity_column)
        for entity_value, group in grouped:
            city_values = set()
            if columns["city"] and columns["city"] in group.columns:
                city_values = {str(value) for value in group[columns["city"]].dropna().astype(str)}
            if not city_values:
                city_values = {value for value in group[tower_column].map(_extract_city_from_tower).dropna().astype(str)}
            spread_rows.append(
                {
                    "entity": entity_value,
                    "tower_count": int(group[tower_column].astype(str).nunique()),
                    "city_count": len(city_values),
                    "file_name": dataset["file_name"],
                }
            )

    spread_rows.sort(key=lambda item: (-item["city_count"], -item["tower_count"], item["entity"]))
    top = spread_rows[0] if spread_rows else None
    return {
        "spread_ranking": spread_rows[:limit],
        "datasets_used": sorted({item["file_name"] for item in spread_rows}),
        "leads": [f"{top['entity']} has the widest location spread in the tower data."] if top else [],
        "alerts": [],
        "visualizations": {"frequency_chart": [{"label": item["entity"], "value": item["city_count"] or item["tower_count"]} for item in spread_rows[:limit]]},
        "response_override": _response_override(
            title=f"Widest Geographic Spread: {top['entity']}" if top else "Tower Spread Ranking",
            direct_answer=f"{top['entity']} appears across {top['city_count']} city marker(s) and {top['tower_count']} tower(s)." if top else "No tower spread data was found.",
            supporting_data=[f"{item['entity']}: {item['city_count']} city marker(s), {item['tower_count']} tower(s)" for item in spread_rows[:limit]],
            analysis="The spread score combines distinct city markers and distinct tower registrations per entity.",
            insight=f"{top['entity']} has the broadest physical footprint in the loaded tower data." if top else "Upload a tower dump dataset to run this analysis.",
            recommended_action="Inspect the top-spread entity's travel sequence and cross-check it with CDR and IPDR activity.",
            focus_entity=top["entity"] if top else None,
        ),
    }


def _session_label(text: str) -> tuple[str | None, set[str]]:
    lowered = text.lower()
    flags: set[str] = set()
    app_name = None
    if any(keyword in lowered for keyword in VPN_KEYWORDS):
        flags.add("vpn")
    if any(keyword in lowered for keyword in TOR_KEYWORDS):
        flags.add("tor")
    for keyword, label in ENCRYPTED_APP_KEYWORDS.items():
        if keyword in lowered:
            flags.add("encrypted_app")
            app_name = label
            break
    if any(keyword in lowered for keyword in SUSPICIOUS_HOST_KEYWORDS):
        flags.add("suspicious_host")
    return app_name, flags


def _extract_ipdr_rows(datasets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for dataset in _ipdr_datasets(datasets):
        columns = _ipdr_columns(dataset)
        entity_column, ip_column, start_column = columns["entity"], columns["ip"], columns["start"]
        if not entity_column or not start_column:
            continue
        working_columns = [column for column in [entity_column, ip_column, columns["host"], columns["app"], columns["upload"], columns["download"], columns["volume"], columns["end"], columns["device"], columns["port"], start_column] if column]
        df = dataset["dataframe"][working_columns].copy()
        df["_ts"] = _coerce_datetime(df[start_column])
        df = df.dropna(subset=["_ts", entity_column])
        for _, row in df.iterrows():
            host_value = ""
            if columns["host"] and columns["host"] in row and pd.notna(row[columns["host"]]):
                host_value = str(row[columns["host"]])
            app_value = ""
            if columns["app"] and columns["app"] in row and pd.notna(row[columns["app"]]):
                app_value = str(row[columns["app"]])
            ip_value = ""
            if columns["ip"] and columns["ip"] in row and pd.notna(row[columns["ip"]]):
                ip_value = str(row[columns["ip"]])
            port_value = ""
            if columns["port"] and columns["port"] in row and pd.notna(row[columns["port"]]):
                port_value = str(row[columns["port"]])
            label_text = " ".join(item for item in [host_value, app_value, ip_value, port_value] if item)
            app_name, flags = _session_label(label_text)
            if ip_value in SUSPICIOUS_IPS:
                flags.add("suspicious_ip")
            upload_value = pd.to_numeric(row[columns["upload"]], errors="coerce") if columns["upload"] and columns["upload"] in row else pd.NA
            download_value = pd.to_numeric(row[columns["download"]], errors="coerce") if columns["download"] and columns["download"] in row else pd.NA
            volume_value = pd.to_numeric(row[columns["volume"]], errors="coerce") if columns["volume"] and columns["volume"] in row else pd.NA
            rows.append(
                {
                    "entity": str(row[entity_column]).strip(),
                    "ip_address": ip_value or None,
                    "host": host_value or None,
                    "application": app_value or app_name,
                    "app_name": app_name,
                    "flags": flags,
                    "timestamp": row["_ts"],
                    "upload": None if pd.isna(upload_value) else float(upload_value),
                    "download": None if pd.isna(download_value) else float(download_value),
                    "volume": None if pd.isna(volume_value) else float(volume_value),
                    "device": str(row[columns["device"]]).strip() if columns["device"] and columns["device"] in row and pd.notna(row[columns["device"]]) else None,
                    "file_name": dataset["file_name"],
                }
            )
    return rows


def analyze_ipdr_vpn_usage(datasets: list[dict[str, Any]]) -> dict[str, Any]:
    sessions = [row for row in _extract_ipdr_rows(datasets) if "vpn" in row["flags"]]
    counter = Counter(row["entity"] for row in sessions)
    ranking = [{"value": value, "count": count} for value, count in counter.most_common(10)]
    top = ranking[0] if ranking else None
    return {
        "vpn_sessions": sessions[:50],
        "vpn_ranking": ranking,
        "datasets_used": sorted({row["file_name"] for row in sessions}),
        "leads": [f"{top['value']} has the highest VPN session count in the IPDR data."] if top else [],
        "alerts": [f"{len(sessions)} VPN-tagged sessions were found in the IPDR data."] if sessions else [],
        "visualizations": {"frequency_chart": [{"label": item["value"], "value": item["count"]} for item in ranking[:8]]},
        "response_override": _response_override(
            title="VPN Usage",
            direct_answer=f"{len(ranking)} subscriber(s) show VPN-tagged sessions." if ranking else "No VPN-tagged sessions were found.",
            supporting_data=[f"{item['value']}: {item['count']} VPN session(s)" for item in ranking[:6]],
            analysis="VPN sessions are detected from domain, application, host, and port keyword matches in IPDR records.",
            insight=f"{top['value']} is the top VPN-using entity in the available IPDR data." if top else "The current IPDR data does not show recognizable VPN indicators.",
            recommended_action="Compare VPN activity times with calls to key contacts and suspicious IP connections.",
            focus_entity=top["value"] if top else None,
        ),
    }


def analyze_ipdr_tor_usage(datasets: list[dict[str, Any]]) -> dict[str, Any]:
    sessions = [row for row in _extract_ipdr_rows(datasets) if "tor" in row["flags"]]
    counter = Counter(row["entity"] for row in sessions)
    ranking = [{"value": value, "count": count} for value, count in counter.most_common(10)]
    top = ranking[0] if ranking else None
    alerts = [f"{row['entity']} connected to TOR-linked activity at {_format_timestamp(row['timestamp'])}." for row in sessions[:3]]
    return {
        "tor_sessions": sessions[:50],
        "tor_ranking": ranking,
        "datasets_used": sorted({row["file_name"] for row in sessions}),
        "leads": [],
        "alerts": alerts,
        "visualizations": {"frequency_chart": [{"label": item["value"], "value": item["count"]} for item in ranking[:8]]},
        "response_override": _response_override(
            title="TOR and Dark-Web Activity",
            direct_answer=f"{len(ranking)} subscriber(s) show TOR-linked session indicators." if ranking else "No TOR-linked sessions were found.",
            supporting_data=[f"{item['value']}: {item['count']} TOR-linked session(s)" for item in ranking[:6]],
            analysis="TOR sessions are detected from host, application, IP, and port indicators such as onion, tor2web, and TOR ports.",
            insight=f"{top['value']} has the strongest TOR-linked activity in the current IPDR data." if top else "The loaded IPDR data does not show TOR indicators.",
            recommended_action="Preserve the flagged sessions and correlate them with night-time calls and suspicious tower activity.",
            focus_entity=top["value"] if top else None,
        ),
    }


def analyze_ipdr_encrypted_apps(datasets: list[dict[str, Any]]) -> dict[str, Any]:
    sessions = [row for row in _extract_ipdr_rows(datasets) if "encrypted_app" in row["flags"]]
    app_counter: Counter[tuple[str, str]] = Counter()
    for row in sessions:
        app_counter.update([(row["entity"], row["application"] or row["app_name"] or "Encrypted App")])
    ranking = [{"entity": entity, "app": app, "count": count} for (entity, app), count in app_counter.most_common(10)]
    return {
        "encrypted_app_sessions": sessions[:50],
        "app_ranking": ranking,
        "datasets_used": sorted({row["file_name"] for row in sessions}),
        "leads": [],
        "alerts": [],
        "visualizations": {"relationship_table": [{"label": f"{item['entity']} / {item['app']}", "value": item["count"]} for item in ranking[:8]]},
        "response_override": _response_override(
            title="Encrypted Messaging Apps",
            direct_answer=f"{len({row['entity'] for row in sessions})} subscriber(s) show encrypted messaging app activity." if sessions else "No encrypted messaging app activity was detected.",
            supporting_data=[f"{item['entity']}: {item['app']} ({item['count']} sessions)" for item in ranking[:8]],
            analysis="Encrypted app usage is classified from host and application keyword matches such as WhatsApp, Telegram, and Signal.",
            insight="The classified app mix shows which subscribers rely on encrypted communication channels." if sessions else "The loaded IPDR data does not expose recognized encrypted app usage.",
            recommended_action="Compare the heaviest encrypted-app sessions with key calls and movement events from the same dates.",
        ),
    }


def analyze_ipdr_suspicious_ips(datasets: list[dict[str, Any]]) -> dict[str, Any]:
    sessions = [row for row in _extract_ipdr_rows(datasets) if "suspicious_ip" in row["flags"] or "suspicious_host" in row["flags"]]
    ip_map: dict[str, set[str]] = defaultdict(set)
    counter: Counter[str] = Counter()
    for row in sessions:
        indicator = row["ip_address"] or row["host"] or "unknown indicator"
        ip_map[indicator].add(row["entity"])
        counter.update([indicator])
    ranking = [{"indicator": indicator, "count": count, "entities": sorted(ip_map[indicator])} for indicator, count in counter.most_common(10)]
    top = ranking[0] if ranking else None
    return {
        "suspicious_ip_events": sessions[:50],
        "indicator_ranking": ranking,
        "datasets_used": sorted({row["file_name"] for row in sessions}),
        "leads": [f"{top['indicator']} is the most repeated suspicious IP or host indicator."] if top else [],
        "alerts": [f"{len(sessions)} suspicious IP/host session(s) were detected."] if sessions else [],
        "visualizations": {"relationship_table": [{"label": item["indicator"], "value": item["count"]} for item in ranking[:8]]},
        "response_override": _response_override(
            title="Suspicious IP Connections",
            direct_answer=f"{len(sessions)} suspicious IP or host connection events were found." if sessions else "No suspicious IP or host indicators were found.",
            supporting_data=[f"{item['indicator']}: {item['count']} session(s) by {', '.join(item['entities'])}" for item in ranking[:6]],
            analysis="Indicators are matched against a built-in suspicious IP list and suspicious host keywords.",
            insight=f"{top['indicator']} is the strongest repeated external indicator in the current IPDR data." if top else "The current IPDR data does not match the suspicious IP watchlist.",
            recommended_action="Prioritize legal and forensic follow-up on the highest-frequency suspicious IP indicators.",
        ),
    }


def analyze_ipdr_upload_download_anomalies(datasets: list[dict[str, Any]]) -> dict[str, Any]:
    sessions = _extract_ipdr_rows(datasets)
    volume_rows = []
    values: list[float] = []
    for row in sessions:
        metric = row["upload"]
        if metric is None:
            metric = row["download"]
        if metric is None:
            metric = row["volume"]
        if metric is None:
            continue
        values.append(metric)
        volume_rows.append({"entity": row["entity"], "metric": metric, "timestamp": row["timestamp"], "file_name": row["file_name"]})
    if not values:
        return {
            "anomalous_sessions": [],
            "datasets_used": [],
            "leads": [],
            "alerts": [],
            "visualizations": {"frequency_chart": []},
            "response_override": _response_override(
                title="Upload and Download Anomalies",
                direct_answer="No upload or volume metrics were found in the IPDR data.",
                supporting_data=[],
                analysis="The loaded IPDR datasets do not include upload, download, or volume fields that can be scored.",
                insight="Upload/download anomaly checks need byte-transfer metrics.",
                recommended_action="Upload IPDR files with upload, download, or total-byte fields.",
            ),
        }
    threshold = median(values) * 2 if median(values) else max(values)
    anomalies = [row for row in volume_rows if row["metric"] >= threshold]
    anomalies.sort(key=lambda item: item["metric"], reverse=True)
    return {
        "anomalous_sessions": anomalies[:20],
        "threshold": threshold,
        "datasets_used": sorted({row["file_name"] for row in anomalies}),
        "leads": [],
        "alerts": [f"{len(anomalies)} IPDR sessions exceed the anomaly threshold of {round(threshold, 2)}."] if anomalies else [],
        "visualizations": {"frequency_chart": [{"label": row["entity"], "value": row["metric"]} for row in anomalies[:8]]},
        "response_override": _response_override(
            title="Upload and Download Anomalies",
            direct_answer=f"{len(anomalies)} IPDR session(s) exceed the anomaly threshold." if anomalies else "No IPDR volume anomalies were detected.",
            supporting_data=[f"{row['entity']}: {round(row['metric'], 2)} at {_format_timestamp(row['timestamp'])}" for row in anomalies[:6]],
            analysis=f"The anomaly threshold is {round(threshold, 2)} based on a median-weighted byte metric.",
            insight="The highest-volume sessions are the best starting point for external transfer review." if anomalies else "The current IPDR volume distribution does not show strong outliers.",
            recommended_action="Cross-check anomalous IPDR sessions with VPN, TOR, and travel events in the same window.",
            focus_entity=anomalies[0]["entity"] if anomalies else None,
        ),
    }


def identify_probable_burner_entity(datasets: list[dict[str, Any]]) -> str | None:
    candidate_scores: Counter[str] = Counter()

    for dataset in _cdr_datasets(datasets):
        columns = _cdr_columns(dataset)
        source, target, time_column = columns["source"], columns["target"], columns["time"]
        if not source or not target or not time_column:
            continue
        df = dataset["dataframe"][[source, target, time_column]].copy()
        df["_ts"] = _coerce_datetime(df[time_column])
        df = df.dropna(subset=["_ts", source, target])
        participants = pd.concat([df[[source]].rename(columns={source: "entity"}), df[[target]].rename(columns={target: "entity"})], ignore_index=True)
        grouped = participants.groupby("entity").size()
        for entity, total in grouped.items():
            entity_rows = df[(df[source].astype(str) == str(entity)) | (df[target].astype(str) == str(entity))]
            if entity_rows.empty:
                continue
            active_days = entity_rows["_ts"].dt.date.nunique()
            unique_contacts = pd.unique(pd.concat([entity_rows[source], entity_rows[target]], ignore_index=True)).size - 1
            night_ratio = round(entity_rows["_ts"].dt.hour.map(lambda hour: _is_between_hours(int(hour), 22, 6)).mean() * 100, 2)
            if active_days <= 7:
                candidate_scores[str(entity)] += 4
            if unique_contacts <= 2:
                candidate_scores[str(entity)] += 3
            if night_ratio >= 50:
                candidate_scores[str(entity)] += 4
            if total <= 10:
                candidate_scores[str(entity)] += 2

    return candidate_scores.most_common(1)[0][0] if candidate_scores else None


def profile_ipdr_entity(datasets: list[dict[str, Any]], entity: str) -> dict[str, Any]:
    sessions = [row for row in _extract_ipdr_rows(datasets) if row["entity"] == entity]
    sessions.sort(key=lambda item: item["timestamp"])
    app_counter: Counter[str] = Counter()
    flags_counter: Counter[str] = Counter()
    for row in sessions:
        app_counter.update([row["application"] or row["app_name"] or row["host"] or row["ip_address"] or "Unknown"])
        flags_counter.update(row["flags"])
    total_volume = sum(row["volume"] or row["upload"] or row["download"] or 0 for row in sessions)
    date_values = [row["timestamp"].date() for row in sessions]
    active_window = (min(date_values), max(date_values)) if date_values else (None, None)
    return {
        "entity": entity,
        "session_count": len(sessions),
        "application_mix": [{"value": value, "count": count} for value, count in app_counter.most_common(8)],
        "flag_mix": [{"value": value, "count": count} for value, count in flags_counter.most_common(8)],
        "active_window": active_window,
        "total_volume": total_volume,
        "datasets_used": sorted({row["file_name"] for row in sessions}),
        "leads": [f"{entity} has {len(sessions)} IPDR session(s) in the active window."] if sessions else [],
        "alerts": [f"{entity} shows only flagged IPDR activity." ] if sessions and len(flags_counter) and sum(flags_counter.values()) >= len(sessions) else [],
        "visualizations": {"frequency_chart": [{"label": item["value"], "value": item["count"]} for item in [{"value": value, "count": count} for value, count in app_counter.most_common(5)]]},
        "response_override": _response_override(
            title=f"IPDR Profile: {entity}",
            direct_answer=f"{entity} has {len(sessions)} IPDR session(s)." if sessions else f"No IPDR sessions were found for {entity}.",
            supporting_data=[
                f"Active window: {_format_date(active_window[0]) if active_window[0] else 'unknown'} to {_format_date(active_window[1]) if active_window[1] else 'unknown'}",
                f"Total transfer metric: {round(total_volume, 2)}",
            ] + [f"{item['value']}: {item['count']} session(s)" for item in [{"value": value, "count": count} for value, count in app_counter.most_common(4)]],
            analysis="The IPDR profile summarizes session count, application mix, flagged indicators, and transfer volume.",
            insight=f"{entity} has a concentrated IPDR footprint during the matched active window." if sessions else f"{entity} does not appear in the loaded IPDR data.",
            recommended_action="Cross-check the IPDR profile with calls, tower hits, and suspicious external indicators.",
            focus_entity=entity,
        ),
    }


def collect_case_events(datasets: list[dict[str, Any]], entity: str | None = None, date_window: dict[str, int | None] | None = None) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []

    for dataset in _cdr_datasets(datasets):
        columns = _cdr_columns(dataset)
        source, target, time_column, duration_column = columns["source"], columns["target"], columns["time"], columns["duration"]
        if not source or not target or not time_column:
            continue
        df = dataset["dataframe"][[source, target, time_column] + ([duration_column] if duration_column else [])].copy()
        df = _filter_by_date_window(df, time_column, date_window)
        df["_ts"] = _coerce_datetime(df[time_column])
        df = df.dropna(subset=["_ts", source, target])
        df[source] = df[source].astype(str).str.strip()
        df[target] = df[target].astype(str).str.strip()
        if entity:
            df = df[(df[source] == entity) | (df[target] == entity)]
        for _, row in df.iterrows():
            events.append(
                {
                    "timestamp": row["_ts"],
                    "dataset_type": "cdr",
                    "file_name": dataset["file_name"],
                    "entity": entity,
                    "summary": f"Call {row[source]} -> {row[target]}",
                    "severity": 1,
                }
            )

    for dataset in _tower_datasets(datasets):
        columns = _tower_columns(dataset)
        entity_column, tower_column, time_column = columns["entity"], columns["tower"], columns["time"]
        if not entity_column or not tower_column or not time_column:
            continue
        df = dataset["dataframe"][[entity_column, tower_column, time_column]].copy()
        df = _filter_by_date_window(df, time_column, date_window)
        df["_ts"] = _coerce_datetime(df[time_column])
        df = df.dropna(subset=["_ts", entity_column, tower_column])
        df[entity_column] = df[entity_column].astype(str).str.strip()
        if entity:
            df = df[df[entity_column] == entity]
        for _, row in df.iterrows():
            events.append(
                {
                    "timestamp": row["_ts"],
                    "dataset_type": "tower",
                    "file_name": dataset["file_name"],
                    "entity": str(row[entity_column]),
                    "summary": f"Tower hit {row[tower_column]} by {row[entity_column]}",
                    "severity": 1,
                }
            )

    for row in _extract_ipdr_rows(datasets):
        if entity and row["entity"] != entity:
            continue
        if date_window:
            ts = pd.Timestamp(row["timestamp"])
            if ts.month != date_window["month"] or ts.day < date_window["start_day"] or ts.day > date_window["end_day"]:
                continue
            if date_window.get("year") and ts.year != date_window["year"]:
                continue
        severity = 2 if {"tor", "vpn", "suspicious_ip"} & row["flags"] else 1
        summary = f"IPDR session by {row['entity']}"
        if row["application"]:
            summary += f" using {row['application']}"
        elif row["host"]:
            summary += f" to {row['host']}"
        events.append(
            {
                "timestamp": row["timestamp"],
                "dataset_type": "ipdr",
                "file_name": row["file_name"],
                "entity": row["entity"],
                "summary": summary,
                "severity": severity,
            }
        )

    events.sort(key=lambda item: item["timestamp"])
    return events


def build_entity_profile(datasets: list[dict[str, Any]], entity: str) -> dict[str, Any]:
    cdr_outgoing = analyze_cdr_outgoing_callers(datasets)
    cdr_calls_to = analyze_cdr_calls_to_entity(datasets, entity)
    tower_movement = analyze_tower_movement(datasets, entity)
    ipdr_profile = profile_ipdr_entity(datasets, entity)
    common_entities = [item for item in find_common_entities_bridge(datasets).get("common_entities", []) if item["value"] == entity]
    events = collect_case_events(datasets, entity=entity)
    return {
        "entity": entity,
        "cdr_summary": {
            "received_calls": cdr_calls_to.get("caller_ranking", []),
            "is_top_caller": bool(cdr_outgoing.get("top_callers")) and cdr_outgoing["top_callers"][0]["value"] == entity,
        },
        "tower_summary": {
            "distinct_towers": tower_movement.get("distinct_towers", []),
            "distinct_cities": tower_movement.get("distinct_cities", []),
        },
        "ipdr_summary": {
            "session_count": ipdr_profile.get("session_count", 0),
            "application_mix": ipdr_profile.get("application_mix", []),
            "flag_mix": ipdr_profile.get("flag_mix", []),
        },
        "cross_dataset_presence": common_entities[0] if common_entities else None,
        "events": events[:30],
        "datasets_used": sorted({event["file_name"] for event in events}),
        "leads": [f"{entity} appears in {len(events)} cross-dataset event(s)."] if events else [],
        "alerts": [f"{entity} has flagged IPDR activity." ] if ipdr_profile.get("flag_mix") else [],
        "visualizations": {"frequency_chart": [{"label": item["value"], "value": item["count"]} for item in ipdr_profile.get("application_mix", [])[:5]]},
        "response_override": _response_override(
            title=f"Complete Profile: {entity}",
            direct_answer=f"{entity} appears across {len({event['dataset_type'] for event in events})} dataset type(s) with {len(events)} matched event(s)." if events else f"No cross-dataset profile was found for {entity}.",
            supporting_data=[
                f"CDR received-call matches: {sum(item['count'] for item in cdr_calls_to.get('caller_ranking', []))}",
                f"Tower spread: {len(tower_movement.get('distinct_towers', []))} tower(s), {len(tower_movement.get('distinct_cities', []))} city marker(s)",
                f"IPDR sessions: {ipdr_profile.get('session_count', 0)}",
            ],
            analysis="The entity profile combines CDR, tower, IPDR, and cross-dataset presence into one view.",
            insight=f"{entity} has a measurable multi-dataset footprint in the current case." if events else f"{entity} does not have a cross-dataset footprint in the loaded case.",
            recommended_action="Review the timeline, strongest contacts, movement path, and flagged internet activity for this entity.",
            focus_entity=entity,
        ),
    }


def reconstruct_critical_window(datasets: list[dict[str, Any]], date_window: dict[str, int | None] | None = None, entity: str | None = None) -> dict[str, Any]:
    events = collect_case_events(datasets, entity=entity, date_window=date_window)
    if not date_window and events:
        best_start = 0
        best_count = 0
        window_size = timedelta(hours=48)
        for index, event in enumerate(events):
            start_time = event["timestamp"]
            end_time = start_time + window_size
            count = sum(1 for candidate in events if start_time <= candidate["timestamp"] <= end_time)
            if count > best_count:
                best_count = count
                best_start = index
        start_time = events[best_start]["timestamp"]
        end_time = start_time + window_size
        events = [event for event in events if start_time <= event["timestamp"] <= end_time]
    dataset_counts = Counter(event["dataset_type"] for event in events)
    alerts = [f"{sum(1 for event in events if event['severity'] > 1)} flagged event(s) appear inside the reconstructed window."] if events else []
    return {
        "critical_events": events[:40],
        "dataset_counts": [{"dataset_type": key, "count": value} for key, value in dataset_counts.items()],
        "datasets_used": sorted({event["file_name"] for event in events}),
        "leads": [f"{len(events)} cross-dataset event(s) were stitched into the critical window."] if events else [],
        "alerts": alerts,
        "visualizations": {"relationship_table": [{"label": item["dataset_type"], "value": item["count"]} for item in [{"dataset_type": key, "count": value} for key, value in dataset_counts.items()]]},
        "response_override": _response_override(
            title="Critical Window Reconstruction",
            direct_answer=f"{len(events)} event(s) were reconstructed in the selected critical window." if events else "No events were found for the requested critical window.",
            supporting_data=[f"{_format_timestamp(event['timestamp'])}: {event['summary']}" for event in events[:8]],
            analysis="The reconstruction merges CDR, tower, and IPDR events into one ordered sequence.",
            insight="The clustered window is the best current period for high-resolution cross-dataset review." if events else "The loaded data does not contain enough matched events for the requested window.",
            recommended_action="Use the reconstructed window to align call activity, location evidence, and internet sessions.",
            focus_entity=entity,
        ),
    }


def score_entity_roles(datasets: list[dict[str, Any]]) -> dict[str, Any]:
    outgoing = analyze_cdr_outgoing_callers(datasets, limit=50).get("top_callers", [])
    common = find_common_entities_bridge(datasets).get("common_entities", [])
    suspicious = detect_suspicious_bridge(datasets)
    tower_spread = analyze_tower_spread(datasets, limit=50).get("spread_ranking", [])
    ipdr_rows = _extract_ipdr_rows(datasets)

    score_map: defaultdict[str, float] = defaultdict(float)
    reasons: defaultdict[str, list[str]] = defaultdict(list)

    for item in outgoing:
        score_map[item["value"]] += item["count"] * 1.5
        reasons[item["value"]].append(f"Outgoing calls: {item['count']}")
    for item in common:
        score_map[item["value"]] += item["file_count"] * 10
        reasons[item["value"]].append(f"Cross-dataset presence: {item['file_count']} dataset(s)")
    for item in tower_spread:
        score_map[item["entity"]] += item["city_count"] * 8 + item["tower_count"] * 2
        reasons[item["entity"]].append(f"Location spread: {item['city_count']} city marker(s), {item['tower_count']} tower(s)")
    for row in ipdr_rows:
        if {"vpn", "tor", "suspicious_ip"} & row["flags"]:
            score_map[row["entity"]] += 6
            reasons[row["entity"]].append("Flagged IPDR activity")
    for text in suspicious.get("alerts", []):
        for value in score_map.keys():
            if value in text:
                score_map[value] += 4

    ranking = [{"entity": entity, "score": round(score, 2), "reasons": reasons[entity][:4]} for entity, score in sorted(score_map.items(), key=lambda item: item[1], reverse=True)]
    top = ranking[0] if ranking else None
    return {
        "role_scores": ranking[:10],
        "datasets_used": [],
        "leads": [f"{top['entity']} has the highest investigation role score."] if top else [],
        "alerts": [],
        "visualizations": {"frequency_chart": [{"label": item["entity"], "value": item["score"]} for item in ranking[:8]]},
        "response_override": _response_override(
            title=f"Highest Role Score: {top['entity']}" if top else "Role Scoring",
            direct_answer=f"{top['entity']} has the highest role score at {top['score']}." if top else "No role scores could be generated.",
            supporting_data=[f"{item['entity']}: {item['score']} ({'; '.join(item['reasons'])})" for item in ranking[:6]],
            analysis="Role scoring combines communication volume, cross-dataset presence, movement spread, and flagged internet activity.",
            insight=f"{top['entity']} is the strongest central entity in the current case graph." if top else "The case does not have enough cross-dataset signals for role scoring.",
            recommended_action="Investigate the top-scoring entities first and verify their strongest evidence chain.",
            focus_entity=top["entity"] if top else None,
        ),
    }


def infer_hierarchy(datasets: list[dict[str, Any]]) -> dict[str, Any]:
    scores = score_entity_roles(datasets).get("role_scores", [])
    if not scores:
        return {
            "hierarchy": [],
            "datasets_used": [],
            "leads": [],
            "alerts": [],
            "visualizations": {"relationship_table": []},
            "response_override": _response_override(
                title="Hierarchy Inference",
                direct_answer="No hierarchy could be inferred.",
                supporting_data=[],
                analysis="Hierarchy inference needs role scores and cross-dataset evidence.",
                insight="The current case does not have enough signals to infer network hierarchy.",
                recommended_action="Load more datasets or run entity profiles first.",
            ),
        }
    hierarchy = []
    for index, item in enumerate(scores[:4]):
        role = "Leader" if index == 0 else "Handler" if index == 1 else "Associate" if index == 2 else "Supporting Node"
        hierarchy.append({"entity": item["entity"], "role": role, "score": item["score"], "reasons": item["reasons"]})
    leader = hierarchy[0]
    return {
        "hierarchy": hierarchy,
        "datasets_used": [],
        "leads": [f"{leader['entity']} is the strongest candidate for the lead role."] if hierarchy else [],
        "alerts": [],
        "visualizations": {"relationship_table": [{"label": f"{item['role']} / {item['entity']}", "value": item["score"]} for item in hierarchy]},
        "response_override": _response_override(
            title=f"Inferred Leader: {leader['entity']}",
            direct_answer=f"{leader['entity']} is the highest-scoring leadership candidate in the current case.",
            supporting_data=[f"{item['role']}: {item['entity']} ({item['score']})" for item in hierarchy],
            analysis="The hierarchy is inferred from role scores rather than from one single metric.",
            insight="The top-ranked entity combines high communication centrality with broad supporting evidence.",
            recommended_action="Validate the inferred leader and handler against exact call chains, location overlap, and flagged internet sessions.",
            focus_entity=leader["entity"],
        ),
    }


def rank_evidence(datasets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    suspicious = detect_suspicious_bridge(datasets)
    for alert in suspicious.get("alerts", [])[:6]:
        evidence.append({"score": 8, "text": alert})
    for lead in suspicious.get("leads", [])[:6]:
        evidence.append({"score": 5, "text": lead})
    role_scores = score_entity_roles(datasets).get("role_scores", [])
    for item in role_scores[:3]:
        evidence.append({"score": 7, "text": f"{item['entity']} role score {item['score']} ({'; '.join(item['reasons'])})"})
    evidence.sort(key=lambda item: (-item["score"], item["text"]))
    return evidence[:10]


def build_final_action_summary(datasets: list[dict[str, Any]]) -> dict[str, Any]:
    hierarchy = infer_hierarchy(datasets).get("hierarchy", [])
    evidence = rank_evidence(datasets)
    top = hierarchy[0] if hierarchy else None
    second = hierarchy[1] if len(hierarchy) > 1 else None
    leads = [item["text"] for item in evidence[:3]]
    return {
        "hierarchy": hierarchy,
        "evidence_ranking": evidence,
        "datasets_used": [],
        "leads": leads,
        "alerts": [f"Top priority entity: {top['entity']}." ] if top else [],
        "visualizations": {"relationship_table": [{"label": item["entity"], "value": item["score"]} for item in hierarchy[:4]]},
        "response_override": _response_override(
            title="Final Investigative Summary",
            direct_answer=(
                f"Primary action target: {top['entity']}."
                if top
                else "A final action summary could not be generated."
            ),
            supporting_data=[
                f"Priority 1: {top['entity']} ({top['role']})" if top else "",
                f"Priority 2: {second['entity']} ({second['role']})" if second else "",
            ] + [item["text"] for item in evidence[:4]],
            analysis="The final action summary combines hierarchy inference with ranked evidence strings from the case.",
            insight="The first arrest or seizure target should be the entity with the strongest combined communication, movement, and flagged activity evidence." if top else "The case does not yet have enough evidence signals for a final action summary.",
            recommended_action="Use the ranked evidence list to prepare arrest, seizure, or legal-process priorities.",
            focus_entity=top["entity"] if top else None,
        ),
    }


def summarize_counter_surveillance(datasets: list[dict[str, Any]]) -> dict[str, Any]:
    tor = analyze_ipdr_tor_usage(datasets)
    vpn = analyze_ipdr_vpn_usage(datasets)
    anomalies = detect_suspicious_bridge(datasets)
    co_flags = []
    if tor.get("tor_sessions"):
        co_flags.append("TOR-linked sessions detected")
    if vpn.get("vpn_sessions"):
        co_flags.append("VPN-tagged sessions detected")
    if anomalies.get("repeated_short_interactions"):
        co_flags.append("Repeated short-duration interactions detected")
    return {
        "counter_surveillance_flags": co_flags,
        "datasets_used": [],
        "leads": co_flags[:3],
        "alerts": [f"{len(co_flags)} counter-surveillance indicator(s) were detected."] if co_flags else [],
        "visualizations": {"relationship_table": [{"label": flag, "value": 1} for flag in co_flags]},
        "response_override": _response_override(
            title="Counter-Surveillance Indicators",
            direct_answer=f"{len(co_flags)} counter-surveillance indicator(s) were detected." if co_flags else "No clear counter-surveillance indicators were detected.",
            supporting_data=co_flags,
            analysis="The indicator list combines TOR use, VPN use, and short operational interaction patterns.",
            insight="Entities tied to multiple indicators deserve higher-priority scrutiny." if co_flags else "The current data does not show a strong counter-surveillance pattern.",
            recommended_action="Compare the flagged indicators with the critical-window reconstruction and top role scores.",
        ),
    }


def find_common_entities_bridge(datasets: list[dict[str, Any]], minimum_dataset_count: int = 2) -> dict[str, Any]:
    from app.services.analysis import find_common_entities

    return find_common_entities(datasets, minimum_dataset_count=minimum_dataset_count)


def detect_suspicious_bridge(datasets: list[dict[str, Any]]) -> dict[str, Any]:
    from app.services.analysis import detect_suspicious_patterns

    return detect_suspicious_patterns(datasets)
