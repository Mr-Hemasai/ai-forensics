from __future__ import annotations

from collections import Counter, defaultdict
from statistics import median
from typing import Any, Optional

import pandas as pd

from app.services.datetime_utils import coerce_datetime


ENTITY_TYPES = {"phone_number", "ip_address", "imei", "imsi", "device_id", "user_id", "tower_id", "location_label"}
SEMANTIC_PRIORITY = {
    "phone_number": 1,
    "ip_address": 2,
    "imei": 3,
    "imsi": 4,
    "device_id": 5,
    "user_id": 6,
    "tower_id": 7,
    "location_label": 8,
}


def _coerce_datetime(series: pd.Series) -> pd.Series:
    return coerce_datetime(series)


def _dataset_profiles(dataset: dict[str, Any]) -> list[dict[str, Any]]:
    return dataset["summary"].get("column_profiles", [])


def _profiles_by_category(dataset: dict[str, Any], categories: set[str]) -> list[dict[str, Any]]:
    return [profile for profile in _dataset_profiles(dataset) if profile["category"] in categories]


def _profiles_by_semantic(dataset: dict[str, Any], semantic_types: set[str]) -> list[dict[str, Any]]:
    return [profile for profile in _dataset_profiles(dataset) if profile["semantic_type"] in semantic_types]


def _clean_values(df: pd.DataFrame, column: str) -> pd.Series:
    values = df[column].dropna().astype(str).str.strip()
    return values[values != ""]


def _profile_lookup(dataset: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {profile["column"]: profile for profile in _dataset_profiles(dataset)}


def _infer_value_semantic(value: str) -> str | None:
    stripped = str(value).strip()
    if "." in stripped and stripped.count(".") == 3:
        return "ip_address"
    if stripped.isdigit():
        if 7 <= len(stripped) <= 13:
            return "phone_number"
        if 14 <= len(stripped) <= 16:
            return "device_id"
    return None


def build_case_profile(datasets: list[dict[str, Any]]) -> dict[str, Any]:
    semantic_inventory: dict[str, list[dict[str, str]]] = defaultdict(list)
    dataset_overview: list[dict[str, Any]] = []

    for dataset in datasets:
        profiles = dataset["summary"]["column_profiles"]
        dataset_overview.append(
            {
                "file_name": dataset["file_name"],
                "row_count": dataset["summary"]["rows"],
                "categories": dataset["summary"]["semantic_summary"]["categories"],
            }
        )
        for profile in profiles:
            if profile["semantic_type"] != "unknown":
                semantic_inventory[profile["semantic_type"]].append(
                    {
                        "file_name": dataset["file_name"],
                        "column": profile["column"],
                        "category": profile["category"],
                    }
                )

    suggestions: list[str] = []
    if semantic_inventory.get("phone_number"):
        suggestions.extend(["Find top phone numbers", "Show late night phone activity"])
    if semantic_inventory.get("ip_address"):
        suggestions.append("Trace IP activity across datasets")
    if semantic_inventory.get("tower_id") or semantic_inventory.get("location_label"):
        suggestions.append("Show location-linked entities")
    if len(datasets) > 1:
        suggestions.append("Find common entities across datasets")

    return {
        "dataset_count": len(datasets),
        "semantic_inventory": dict(semantic_inventory),
        "dataset_overview": dataset_overview,
        "suggestions": suggestions[:6],
    }


def analyze_frequency(datasets: list[dict[str, Any]], limit: int = 10) -> dict[str, Any]:
    global_counter: Counter[str] = Counter()
    per_file: list[dict[str, Any]] = []

    for dataset in datasets:
        df: pd.DataFrame = dataset["dataframe"]
        file_counter: Counter[str] = Counter()
        entity_profiles = _profiles_by_category(dataset, {"entity", "relationship"})

        for profile in entity_profiles:
            values = _clean_values(df, profile["column"])
            file_counter.update(values.tolist())
            global_counter.update(values.tolist())

        per_file.append(
            {
                "file_name": dataset["file_name"],
                "top_entities": [{"value": value, "count": count} for value, count in file_counter.most_common(limit)],
            }
        )

    top_entities = [{"value": value, "count": count} for value, count in global_counter.most_common(limit)]
    chart = [{"label": item["value"], "value": item["count"]} for item in top_entities[:8]]
    return {"top_entities": top_entities, "per_file": per_file, "visualizations": {"frequency_chart": chart}}


def analyze_phone_number_frequency(datasets: list[dict[str, Any]], limit: int = 10) -> dict[str, Any]:
    global_counter: Counter[str] = Counter()
    datasets_used: list[str] = []

    for dataset in datasets:
        df: pd.DataFrame = dataset["dataframe"]
        phone_profiles = _profiles_by_semantic(dataset, {"phone_number"})
        if not phone_profiles:
            continue
        datasets_used.append(dataset["file_name"])
        for profile in phone_profiles:
            values = _clean_values(df, profile["column"])
            global_counter.update(values.tolist())

    ranking = [{"value": value, "count": count} for value, count in global_counter.most_common(limit)]
    top = ranking[0] if ranking else None
    return {
        "top_phone_numbers": ranking,
        "datasets_used": datasets_used,
        "leads": [f"{top['value']} is the most active phone number in the loaded case data."] if top else [],
        "alerts": [],
        "visualizations": {"frequency_chart": [{"label": item["value"], "value": item["count"]} for item in ranking[:8]]},
        "response_override": {
            "title": f"Top Phone Number: {top['value']}" if top else "Phone Number Ranking",
            "direct_answer": f"{top['value']} has the highest phone-number activity with {top['count']} records." if top else "No phone-number fields were found in the loaded datasets.",
            "supporting_data": [f"{item['value']}: {item['count']} records" for item in ranking[:8]],
            "analysis": (
                f"This ranking uses only columns classified as phone numbers. {top['value']} is ahead of {ranking[1]['value']} by {top['count'] - ranking[1]['count']} records."
                if len(ranking) > 1
                else "This ranking uses only columns classified as phone numbers."
            ),
            "insight": f"{top['value']} is the strongest phone-number anchor in the current case." if top else "Upload telecom data with phone-number columns to run this analysis.",
            "recommended_action": "Check the top phone number's contacts, night activity, and cross-dataset presence.",
            "focus_entity": top["value"] if top else None,
            "suggestions": ["Who called that number?", "Show their night activity", "Find common entities across datasets"],
        },
    }


def detect_time_patterns(datasets: list[dict[str, Any]], night_start: int = 0, night_end: int = 5) -> dict[str, Any]:
    patterns: list[dict[str, Any]] = []
    timeline_points: list[dict[str, Any]] = []

    for dataset in datasets:
        df: pd.DataFrame = dataset["dataframe"]
        time_profiles = _profiles_by_category(dataset, {"time"})
        entity_profiles = _profiles_by_category(dataset, {"entity", "relationship"})

        for profile in time_profiles:
            parsed = _coerce_datetime(df[profile["column"]])
            working = df.copy()
            working["_ts"] = parsed
            working = working.dropna(subset=["_ts"])
            if working.empty:
                continue

            working["_hour"] = working["_ts"].dt.hour
            working["_day"] = working["_ts"].dt.day_name()
            night_df = working[(working["_hour"] >= night_start) & (working["_hour"] <= night_end)]
            hourly_distribution = working["_hour"].value_counts().sort_index()
            day_distribution = working["_day"].value_counts()

            top_night_entities: list[dict[str, Any]] = []
            for entity_profile in entity_profiles[:2]:
                counts = (
                    night_df[entity_profile["column"]]
                    .dropna()
                    .astype(str)
                    .value_counts()
                    .head(3)
                    .reset_index()
                    .values.tolist()
                )
                top_night_entities.extend(
                    [
                        {"column": entity_profile["column"], "value": item[0], "count": int(item[1])}
                        for item in counts
                    ]
                )

            patterns.append(
                {
                    "file_name": dataset["file_name"],
                    "time_column": profile["column"],
                    "night_activity_count": int(len(night_df)),
                    "night_activity_ratio": round((len(night_df) / len(working)) * 100, 2),
                    "peak_hour": int(hourly_distribution.idxmax()),
                    "peak_hour_count": int(hourly_distribution.max()),
                    "hourly_distribution": {str(int(hour)): int(count) for hour, count in hourly_distribution.items()},
                    "day_distribution": {str(day): int(count) for day, count in day_distribution.items()},
                    "night_entities": top_night_entities[:5],
                }
            )

            for hour, count in hourly_distribution.items():
                timeline_points.append(
                    {"dataset": dataset["file_name"], "bucket": f"{int(hour):02d}:00", "value": int(count)}
                )

    return {"time_patterns": patterns, "visualizations": {"timeline": timeline_points}}


def detect_relationships(datasets: list[dict[str, Any]]) -> dict[str, Any]:
    relationships: list[dict[str, Any]] = []
    graph_edges: list[dict[str, Any]] = []

    for dataset in datasets:
        df: pd.DataFrame = dataset["dataframe"]
        pairs = dataset["summary"]["semantic_summary"].get("relationship_pairs", [])
        for pair in pairs:
            source, target = pair["source"], pair["target"]
            relation_df = df[[source, target]].dropna().astype(str)
            if relation_df.empty:
                continue

            pair_counts = relation_df.value_counts().head(12).reset_index(name="count")
            top_pairs = []
            for _, row in pair_counts.iterrows():
                item = {"source": row[source], "target": row[target], "count": int(row["count"])}
                top_pairs.append(item)
                graph_edges.append({"source": item["source"], "target": item["target"], "value": item["count"]})

            relationships.append(
                {"file_name": dataset["file_name"], "source_column": source, "target_column": target, "pairs": top_pairs}
            )

    return {"relationships": relationships, "visualizations": {"network_edges": graph_edges[:20]}}


def _collect_relationship_rows(
    datasets: list[dict[str, Any]],
    entity: str,
    direction: str,
) -> tuple[list[dict[str, Any]], list[str]]:
    preferred_rows: list[dict[str, Any]] = []
    fallback_rows: list[dict[str, Any]] = []
    datasets_used: list[str] = []
    expected_semantic = _infer_value_semantic(entity)

    for dataset in datasets:
        df: pd.DataFrame = dataset["dataframe"]
        profile_map = _profile_lookup(dataset)
        for pair in dataset["summary"]["semantic_summary"].get("relationship_pairs", []):
            source, target = pair["source"], pair["target"]
            if profile_map.get(source, {}).get("role") != "source" or profile_map.get(target, {}).get("role") != "target":
                continue
            subset = df[[source, target]].dropna().astype(str)
            if subset.empty:
                continue

            if direction == "outgoing":
                matched = subset[subset[source].str.strip() == entity]
                counterpart_column = target
            else:
                matched = subset[subset[target].str.strip() == entity]
                counterpart_column = source

            if matched.empty:
                continue

            grouped = matched[counterpart_column].str.strip().value_counts().reset_index()
            grouped.columns = ["counterpart", "count"]
            datasets_used.append(dataset["file_name"])
            source_semantic = profile_map.get(source, {}).get("semantic_type")
            target_semantic = profile_map.get(target, {}).get("semantic_type")
            pair_matches_expected = (
                expected_semantic is None
                or (source_semantic == expected_semantic and target_semantic == expected_semantic)
            )
            for _, row in grouped.iterrows():
                item = {
                    "dataset": dataset["file_name"],
                    "counterpart": row["counterpart"],
                    "count": int(row["count"]),
                    "source_column": source,
                    "target_column": target,
                }
                if pair_matches_expected:
                    preferred_rows.append(item)
                else:
                    fallback_rows.append(item)

    contact_rows = preferred_rows or fallback_rows
    return contact_rows, datasets_used


def find_top_contacts(datasets: list[dict[str, Any]], entity: str, direction: str) -> dict[str, Any]:
    contact_rows, datasets_used = _collect_relationship_rows(datasets, entity, direction)
    if not contact_rows:
        return {
            "entity": entity,
            "relationship_direction": direction,
            "contact_ranking": [],
            "datasets_used": [],
            "leads": [],
            "alerts": [],
            "visualizations": {"relationship_table": []},
        }

    aggregate_counter: Counter[str] = Counter()
    for row in contact_rows:
        aggregate_counter[row["counterpart"]] += row["count"]

    ranking = [{"value": value, "count": count} for value, count in aggregate_counter.most_common(10)]
    top_contact = ranking[0] if ranking else None
    leads: list[str] = []
    alerts: list[str] = []
    if top_contact:
        leads.append(
            f"{entity} {'called' if direction == 'outgoing' else 'was contacted by'} {top_contact['value']} {top_contact['count']} times."
        )
        if top_contact["count"] >= 3:
            alerts.append(
                f"{entity} has repeated {'outgoing' if direction == 'outgoing' else 'incoming'} contact with {top_contact['value']}."
            )

    return {
        "entity": entity,
        "relationship_direction": direction,
        "top_contact": top_contact,
        "contact_ranking": ranking,
        "contact_rows": sorted(contact_rows, key=lambda item: item["count"], reverse=True)[:15],
        "datasets_used": sorted(set(datasets_used)),
        "leads": leads[:5],
        "alerts": alerts[:5],
        "visualizations": {"relationship_table": ranking[:10]},
    }


def detect_entity_time_patterns(
    datasets: list[dict[str, Any]],
    entity: str,
    night_start: int = 0,
    night_end: int = 5,
) -> dict[str, Any]:
    hourly_counter: Counter[int] = Counter()
    dataset_breakdown: list[dict[str, Any]] = []
    total_hits = 0
    night_hits = 0
    datasets_used: list[str] = []

    for dataset in datasets:
        df: pd.DataFrame = dataset["dataframe"]
        time_profiles = _profiles_by_category(dataset, {"time"})
        entity_profiles = _profiles_by_category(dataset, {"entity", "relationship"})
        if not time_profiles or not entity_profiles:
            continue

        match_mask = pd.Series(False, index=df.index)
        for profile in entity_profiles:
            column_match = df[profile["column"]].fillna("").astype(str).str.strip() == entity
            match_mask = match_mask | column_match

        subset = df[match_mask].copy()
        if subset.empty:
            continue

        time_column = time_profiles[0]["column"]
        subset["_ts"] = _coerce_datetime(subset[time_column])
        subset = subset.dropna(subset=["_ts"])
        if subset.empty:
            continue

        subset["_hour"] = subset["_ts"].dt.hour
        counts = subset["_hour"].value_counts().sort_index()
        file_total = int(len(subset))
        file_night = int(subset[(subset["_hour"] >= night_start) & (subset["_hour"] <= night_end)].shape[0])
        total_hits += file_total
        night_hits += file_night
        datasets_used.append(dataset["file_name"])

        for hour, count in counts.items():
            hourly_counter[int(hour)] += int(count)

        dataset_breakdown.append(
            {
                "file_name": dataset["file_name"],
                "time_column": time_column,
                "total_hits": file_total,
                "night_hits": file_night,
                "night_ratio": round((file_night / file_total) * 100, 2) if file_total else 0.0,
            }
        )

    peak_hour = max(hourly_counter, key=hourly_counter.get) if hourly_counter else None
    night_ratio = round((night_hits / total_hits) * 100, 2) if total_hits else 0.0
    leads: list[str] = []
    alerts: list[str] = []

    if total_hits:
        leads.append(f"{entity} appears in {total_hits} timed records.")
    if night_hits:
        leads.append(f"{entity} appears in {night_hits} night records.")
    if night_ratio >= 25:
        alerts.append(f"{entity} has {night_ratio}% activity during night hours.")

    return {
        "entity": entity,
        "total_hits": total_hits,
        "night_hits": night_hits,
        "night_ratio": night_ratio,
        "peak_hour": peak_hour,
        "peak_hour_count": hourly_counter.get(peak_hour, 0) if peak_hour is not None else 0,
        "hourly_distribution": {f"{hour:02d}:00": count for hour, count in sorted(hourly_counter.items())},
        "dataset_breakdown": dataset_breakdown,
        "datasets_used": datasets_used,
        "leads": leads[:5],
        "alerts": alerts[:5],
        "visualizations": {
            "time_chart": [{"bucket": bucket, "value": value} for bucket, value in {f"{hour:02d}:00": count for hour, count in sorted(hourly_counter.items())}.items()]
        },
    }


def find_common_entities(datasets: list[dict[str, Any]], minimum_dataset_count: int = 2) -> dict[str, Any]:
    presence_map: dict[str, dict[str, Any]] = {}

    for dataset in datasets:
        df: pd.DataFrame = dataset["dataframe"]
        for profile in _profiles_by_semantic(dataset, ENTITY_TYPES):
            values = set(_clean_values(df, profile["column"]).tolist())
            for value in values:
                entry = presence_map.setdefault(
                    value,
                    {"value": value, "files": set(), "columns": defaultdict(set), "semantic_types": set()},
                )
                entry["files"].add(dataset["file_name"])
                entry["columns"][dataset["file_name"]].add(profile["column"])
                entry["semantic_types"].add(profile["semantic_type"])

    common_entities: list[dict[str, Any]] = []
    for item in presence_map.values():
        file_count = len(item["files"])
        if file_count < minimum_dataset_count:
            continue
        common_entities.append(
            {
                "value": item["value"],
                "file_count": file_count,
                "files": sorted(item["files"]),
                "columns": {key: sorted(value) for key, value in item["columns"].items()},
                "semantic_types": sorted(item["semantic_types"]),
            }
        )

    common_entities.sort(
        key=lambda item: (
            -item["file_count"],
            min(SEMANTIC_PRIORITY.get(semantic_type, 99) for semantic_type in item["semantic_types"]),
            item["value"],
        )
    )
    return {"common_entities": common_entities[:20]}


def extract_unique_entities(datasets: list[dict[str, Any]]) -> dict[str, Any]:
    results: list[dict[str, Any]] = []

    for dataset in datasets:
        df: pd.DataFrame = dataset["dataframe"]
        per_file: dict[str, int] = {}
        for profile in _profiles_by_category(dataset, {"entity", "relationship"}):
            per_file[profile["column"]] = int(_clean_values(df, profile["column"]).nunique())
        results.append({"file_name": dataset["file_name"], "unique_entities": per_file})

    return {"unique_entities": results}


def detect_outliers(datasets: list[dict[str, Any]]) -> dict[str, Any]:
    frequency = analyze_frequency(datasets, limit=50)["top_entities"]
    counts = [item["count"] for item in frequency]
    if len(counts) < 4:
        return {"outliers": []}

    med = median(counts)
    threshold = med * 2 if med else max(counts)
    outliers = [item for item in frequency if item["count"] >= threshold and item["count"] > med]
    return {"outliers": outliers[:10], "threshold": threshold}


def detect_suspicious_patterns(datasets: list[dict[str, Any]]) -> dict[str, Any]:
    frequency_result = analyze_frequency(datasets, limit=15)
    time_result = detect_time_patterns(datasets)
    relationship_result = detect_relationships(datasets)
    common_result = find_common_entities(datasets)
    outlier_result = detect_outliers(datasets)

    leads: list[str] = []
    alerts: list[str] = []

    for entity in frequency_result["top_entities"][:5]:
        if entity["count"] >= 10:
            alerts.append(f"{entity['value']} shows unusually high activity with {entity['count']} records.")
        else:
            leads.append(f"{entity['value']} has repeated activity worth review ({entity['count']} records).")

    for item in common_result["common_entities"][:5]:
        if item["file_count"] >= 3:
            alerts.append(f"{item['value']} appears across {item['file_count']} datasets, indicating strong cross-source relevance.")
        else:
            leads.append(f"{item['value']} is shared across {item['file_count']} datasets.")

    for pattern in time_result["time_patterns"][:5]:
        if pattern["night_activity_ratio"] >= 25:
            alerts.append(
                f"{pattern['file_name']} has {pattern['night_activity_ratio']}% late-night activity in {pattern['time_column']}."
            )

    for relationship in relationship_result["relationships"][:3]:
        if relationship["pairs"]:
            top_pair = relationship["pairs"][0]
            if top_pair["count"] >= 3:
                leads.append(
                    f"Repeated link observed between {top_pair['source']} and {top_pair['target']} ({top_pair['count']} interactions)."
                )

    for outlier in outlier_result["outliers"][:3]:
        alerts.append(f"{outlier['value']} is a count outlier compared with the case median activity.")

    repeated_short_interactions: list[dict[str, Any]] = []
    for dataset in datasets:
        df: pd.DataFrame = dataset["dataframe"]
        duration_columns = [profile["column"] for profile in _profiles_by_semantic(dataset, {"duration"})]
        pair_columns = dataset["summary"]["semantic_summary"].get("relationship_pairs", [])
        if not duration_columns or not pair_columns:
            continue

        duration_column = duration_columns[0]
        pair = pair_columns[0]
        subset = df[[pair["source"], pair["target"], duration_column]].dropna().copy()
        if subset.empty:
            continue
        subset[duration_column] = pd.to_numeric(subset[duration_column], errors="coerce")
        subset = subset[subset[duration_column] <= 60]
        grouped = subset.groupby([pair["source"], pair["target"]]).size().reset_index(name="count")
        grouped = grouped[grouped["count"] >= 3].sort_values("count", ascending=False)
        for _, row in grouped.head(3).iterrows():
            repeated_short_interactions.append(
                {
                    "file_name": dataset["file_name"],
                    "source": str(row[pair["source"]]),
                    "target": str(row[pair["target"]]),
                    "count": int(row["count"]),
                }
            )
            alerts.append(
                f"Short repeated interactions detected between {row[pair['source']]} and {row[pair['target']]} in {dataset['file_name']}."
            )

    return {
        "frequency_snapshot": frequency_result["top_entities"][:10],
        "time_snapshot": time_result["time_patterns"][:5],
        "relationship_snapshot": relationship_result["relationships"][:5],
        "cross_dataset_snapshot": common_result["common_entities"][:10],
        "outlier_snapshot": outlier_result["outliers"][:10],
        "repeated_short_interactions": repeated_short_interactions[:10],
        "leads": leads[:6],
        "alerts": alerts[:6],
        "visualizations": {
            **frequency_result.get("visualizations", {}),
            **time_result.get("visualizations", {}),
            **relationship_result.get("visualizations", {}),
        },
    }


def build_entity_timeline(datasets: list[dict[str, Any]], entity: Optional[str] = None, limit: int = 50) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []

    for dataset in datasets:
        df: pd.DataFrame = dataset["dataframe"]
        entity_profiles = _profiles_by_category(dataset, {"entity", "relationship"})
        time_profiles = _profiles_by_category(dataset, {"time"})
        if not entity_profiles:
            continue

        match_mask = pd.Series(True, index=df.index) if not entity else pd.Series(False, index=df.index)
        matched_columns: list[str] = []
        for profile in entity_profiles:
            if entity:
                column_match = df[profile["column"]].fillna("").astype(str).str.strip() == entity
                if column_match.any():
                    match_mask = match_mask | column_match
                    matched_columns.append(profile["column"])

        subset = df[match_mask].copy()
        if subset.empty:
            continue

        for _, row in subset.iterrows():
            timestamp = None
            for time_profile in time_profiles:
                parsed = pd.to_datetime(row[time_profile["column"]], errors="coerce")
                if pd.notna(parsed):
                    timestamp = parsed
                    break

            summary_parts = []
            for column in matched_columns[:3]:
                summary_parts.append(f"{column}={row.get(column, '')}")
            events.append(
                {
                    "file_name": dataset["file_name"],
                    "timestamp": timestamp.isoformat() if timestamp is not None else None,
                    "summary": " | ".join(summary_parts)
                    or (f"Matched entity in {dataset['file_name']}" if entity else f"Event in {dataset['file_name']}"),
                }
            )

    events.sort(key=lambda item: item["timestamp"] or "")
    return events[:limit]


def build_entity_drilldown(datasets: list[dict[str, Any]], entity: str) -> dict[str, Any]:
    frequency = analyze_frequency(datasets, limit=100)["top_entities"]
    common_entities = find_common_entities(datasets, minimum_dataset_count=1)["common_entities"]
    relationships = detect_relationships(datasets)["relationships"]
    time_patterns = detect_time_patterns(datasets)["time_patterns"]
    timeline = build_entity_timeline(datasets, entity)

    total_occurrences = next((item["count"] for item in frequency if item["value"] == entity), 0)
    dataset_presence = next((item["file_count"] for item in common_entities if item["value"] == entity), 1)
    night_hits = 0
    for pattern in time_patterns:
        for item in pattern.get("night_entities", []):
            if item["value"] == entity:
                night_hits += item["count"]

    connections: list[dict[str, Any]] = []
    for relationship in relationships:
        for pair in relationship["pairs"]:
            if pair["source"] == entity or pair["target"] == entity:
                counterpart = pair["target"] if pair["source"] == entity else pair["source"]
                connections.append({"counterpart": counterpart, "count": pair["count"], "file_name": relationship["file_name"]})

    suspicion_score = min(100, total_occurrences * 3 + dataset_presence * 15 + night_hits * 2)
    suspicion_level = "High" if suspicion_score >= 70 else "Medium" if suspicion_score >= 35 else "Low"

    return {
        "entity": entity,
        "total_occurrences": total_occurrences,
        "dataset_presence": dataset_presence,
        "night_hits": night_hits,
        "suspicion_score": suspicion_score,
        "suspicion_level": suspicion_level,
        "connections": sorted(connections, key=lambda item: item["count"], reverse=True)[:10],
        "timeline": timeline,
    }
