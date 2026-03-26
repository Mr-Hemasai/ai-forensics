from __future__ import annotations

from typing import Any

from app.core.store import CaseRecord, default_case_context
from app.services.ai_formatter import enhance_response_card
from app.services.analysis import (
    analyze_frequency,
    analyze_phone_number_frequency,
    build_case_profile,
    detect_entity_time_patterns,
    detect_outliers,
    detect_relationships,
    detect_suspicious_patterns,
    detect_time_patterns,
    extract_unique_entities,
    find_common_entities,
    find_top_contacts,
)
from app.services.forensic_analytics import (
    analyze_cdr_calls_to_entity,
    analyze_cdr_day_week_patterns,
    analyze_cdr_incoming_receivers,
    analyze_cdr_night_calls,
    analyze_cdr_outgoing_callers,
    analyze_cdr_pair_history,
    analyze_ipdr_encrypted_apps,
    analyze_ipdr_suspicious_ips,
    trace_ip_activity_across_datasets,
    analyze_ipdr_tor_usage,
    analyze_ipdr_upload_download_anomalies,
    analyze_ipdr_vpn_usage,
    analyze_tower_colocation,
    analyze_tower_movement,
    analyze_tower_spread,
    analyze_tower_top_hits,
    build_entity_profile,
    build_final_action_summary,
    identify_probable_burner_entity,
    infer_hierarchy,
    parse_date_window,
    profile_burner_cdr_entity,
    profile_ipdr_entity,
    reconstruct_critical_window,
    score_entity_roles,
    summarize_counter_surveillance,
)
from app.services.intent import detect_intent
from app.services.response_builder import build_response_card, extract_observation_points, response_card_to_text


def _prepare_case_datasets(case_record: CaseRecord) -> list[dict[str, Any]]:
    return [
        {"file_name": dataset.file_name, "dataframe": dataset.dataframe, "summary": dataset.summary}
        for dataset in case_record.datasets
    ]


def build_case_overview(case_record: CaseRecord, case_profile: dict[str, Any]) -> dict[str, Any]:
    datasets = _prepare_case_datasets(case_record)
    frequency = analyze_frequency(datasets, limit=5) if datasets else {"top_entities": [], "visualizations": {}}
    shared = find_common_entities(datasets) if len(datasets) > 1 else {"common_entities": []}
    return {
        "case_name": case_record.case_name,
        "dataset_count": len(case_record.datasets),
        "datasets": [dataset.summary for dataset in case_record.datasets],
        "case_profile": case_profile,
        "top_entities": frequency["top_entities"],
        "common_entities": shared["common_entities"],
        "visualizations": frequency.get("visualizations", {}),
        "leads": [
            f"{dataset.file_name} contains {dataset.summary['rows']} rows and {len(dataset.summary['columns'])} columns."
            for dataset in case_record.datasets[:3]
        ],
        "alerts": [
            "Cross-dataset matching is available because multiple datasets are loaded."
            if len(case_record.datasets) > 1
            else "Only one dataset is loaded. Add more files for stronger correlation."
        ],
    }


def _build_reference_prompt(context: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    last_entity = context.get("last_entity")
    if last_entity:
        direct_answer = f"I need a reference entity. Do you want to analyze {last_entity} (last active entity)?"
        leads = [f"Last active entity in this case: {last_entity}."]
    else:
        direct_answer = "Please specify the entity to continue analysis."
        leads = ["Accepted entities include phone numbers, IP addresses, IMEI, IMSI, and similar IDs."]

    structured_result = {"leads": leads, "alerts": [], "visualizations": {}}
    response_card = {
        "title": "Reference Needed",
        "direct_answer": direct_answer,
        "supporting_data": leads[:1],
        "analysis": "The current query needs a specific entity for accurate filtering.",
        "insight": "The system does not guess the entity when the query is incomplete.",
        "recommended_action": "Send the entity value or confirm the last active entity.",
        "leads": leads[:3],
        "alerts": [],
        "suggestions": [f"Analyze {last_entity}", "Show their night activity"] if last_entity else ["Show most active entities"],
        "focus_entity": last_entity,
    }
    return structured_result, response_card


def _update_context(case_record: CaseRecord, intent: str, query_type: str, focus_entity: str | None, structured_result: dict[str, Any]) -> None:
    context = dict(case_record.context or default_case_context())
    context["last_intent"] = intent
    context["last_query_type"] = query_type
    context["last_entity"] = focus_entity or context.get("last_entity")
    datasets_used = structured_result.get("datasets_used") or []
    context["last_dataset_used"] = datasets_used[0] if datasets_used else context.get("last_dataset_used")
    case_record.context = context


def run_query(case_record: CaseRecord, message: str) -> dict[str, Any]:
    datasets = _prepare_case_datasets(case_record)
    case_profile = build_case_profile(datasets)
    case_context = dict(case_record.context or default_case_context())
    intent_info = detect_intent(message, case_context)
    intent = intent_info["intent"]
    query_type = intent_info["query_type"]
    entity = intent_info["entity"]
    entities = intent_info.get("entities", [])
    date_window = intent_info.get("date_window") or parse_date_window(message)
    context_used = entity if intent_info.get("used_context") and entity else None
    burner_entity = identify_probable_burner_entity(datasets) if intent_info.get("burner_requested") else None
    if intent_info.get("burner_requested") and not entity and query_type in {"burner_cdr_profile", "burner_ipdr_profile", "entity_profile", "tower_movement"}:
        entity = burner_entity

    if not datasets:
        structured_result = {
            "leads": ["Upload at least one CSV or Excel file to start analysis."],
            "alerts": ["No datasets are available in this case yet."],
            "visualizations": {},
        }
        response_card = build_response_card("overview", message, structured_result, case_profile)
        return {
            "intent": "overview",
            "structured_result": structured_result,
            "response_card": response_card,
            "reply": response_card_to_text(response_card),
            "case_profile": case_profile,
            "observation_items": case_record.observation_items,
        }

    if intent_info.get("requires_entity") and not entity:
        structured_result, response_card = _build_reference_prompt(case_context)
        reply = response_card_to_text(response_card)
        return {
            "intent": intent,
            "structured_result": structured_result,
            "response_card": response_card,
            "reply": reply,
            "case_profile": case_profile,
            "observation_items": case_record.observation_items,
        }

    if query_type == "cdr_top_callers":
        structured_result = analyze_cdr_outgoing_callers(datasets)
    elif query_type == "cdr_top_receivers":
        structured_result = analyze_cdr_incoming_receivers(datasets)
    elif query_type == "calls_to_entity" and entity:
        structured_result = analyze_cdr_calls_to_entity(datasets, entity)
    elif query_type == "cdr_night_calls":
        structured_result = analyze_cdr_night_calls(datasets)
    elif query_type == "top_phone_numbers":
        structured_result = analyze_phone_number_frequency(datasets)
    elif query_type == "cross_dataset_ip_activity":
        structured_result = trace_ip_activity_across_datasets(datasets)
    elif query_type == "cdr_pair_history" and len(entities) >= 2:
        structured_result = analyze_cdr_pair_history(datasets, entities[0], entities[1])
    elif query_type == "cdr_pair_history_night" and len(entities) >= 2:
        structured_result = analyze_cdr_pair_history(datasets, entities[0], entities[1], night_only=True)
    elif query_type == "cdr_day_week_patterns":
        if len(entities) >= 2:
            structured_result = analyze_cdr_day_week_patterns(datasets, pair=(entities[0], entities[1]))
        else:
            structured_result = analyze_cdr_day_week_patterns(datasets, entity=entity)
    elif query_type == "burner_cdr_profile" and entity:
        structured_result = profile_burner_cdr_entity(datasets, entity)
    elif query_type == "tower_top_hits":
        structured_result = analyze_tower_top_hits(datasets)
    elif query_type == "tower_colocation":
        if len(entities) >= 2:
            structured_result = analyze_tower_colocation(datasets, entities[0], entities[1])
        elif burner_entity and entities:
            structured_result = analyze_tower_colocation(datasets, burner_entity, entities[0])
        elif burner_entity and entity and burner_entity != entity:
            structured_result = analyze_tower_colocation(datasets, burner_entity, entity)
        else:
            structured_result = build_case_overview(case_record, case_profile)
    elif query_type == "tower_movement" and entity:
        structured_result = analyze_tower_movement(datasets, entity)
    elif query_type == "tower_spread":
        structured_result = analyze_tower_spread(datasets)
    elif query_type == "vpn_usage":
        structured_result = analyze_ipdr_vpn_usage(datasets)
    elif query_type == "tor_usage":
        structured_result = analyze_ipdr_tor_usage(datasets)
    elif query_type == "encrypted_apps":
        structured_result = analyze_ipdr_encrypted_apps(datasets)
    elif query_type == "suspicious_ips":
        structured_result = analyze_ipdr_suspicious_ips(datasets)
    elif query_type == "upload_download_anomalies":
        structured_result = analyze_ipdr_upload_download_anomalies(datasets)
    elif query_type == "burner_ipdr_profile" and entity:
        structured_result = profile_ipdr_entity(datasets, entity)
    elif query_type == "entity_profile" and entity:
        structured_result = build_entity_profile(datasets, entity)
    elif query_type == "critical_window":
        structured_result = reconstruct_critical_window(datasets, date_window=date_window, entity=entity)
    elif query_type == "hierarchy_inference":
        structured_result = infer_hierarchy(datasets)
    elif query_type == "counter_surveillance":
        structured_result = summarize_counter_surveillance(datasets)
    elif query_type == "final_action_summary":
        structured_result = build_final_action_summary(datasets)
    elif query_type == "role_scoring":
        structured_result = score_entity_roles(datasets)
    elif intent == "frequency":
        structured_result = analyze_frequency(datasets)
    elif intent == "time" and entity:
        structured_result = detect_entity_time_patterns(datasets, entity)
    elif intent == "time":
        structured_result = detect_time_patterns(datasets)
    elif intent == "relationship" and query_type == "outgoing_calls" and entity:
        structured_result = find_top_contacts(datasets, entity, "outgoing")
    elif intent == "relationship" and query_type == "incoming_calls" and entity:
        structured_result = find_top_contacts(datasets, entity, "incoming")
    elif intent == "relationship":
        structured_result = detect_relationships(datasets)
    elif intent == "cross_dataset":
        structured_result = find_common_entities(datasets)
    elif intent == "anomaly":
        structured_result = detect_suspicious_patterns(datasets)
    elif intent == "unique_entities":
        structured_result = extract_unique_entities(datasets)
    else:
        structured_result = build_case_overview(case_record, case_profile)

    if intent == "anomaly":
        outliers = detect_outliers(datasets)
        structured_result.setdefault("outlier_snapshot", outliers.get("outliers", []))

    response_card = build_response_card(intent, message, structured_result, case_profile, focus_entity=entity)
    response_card, ai_metadata = enhance_response_card(response_card, intent, message, structured_result)
    if context_used:
        response_card["context_used"] = context_used
    reply = response_card_to_text(response_card)

    for item in extract_observation_points(response_card, structured_result):
        if item not in case_record.observation_items:
            case_record.observation_items.append(item)
    case_record.observation_items = case_record.observation_items[-20:]

    _update_context(case_record, intent, query_type, response_card.get("focus_entity") or entity, structured_result)

    return {
        "intent": intent,
        "structured_result": structured_result,
        "response_card": response_card,
        "reply": reply,
        "case_profile": case_profile,
        "observation_items": case_record.observation_items,
        "ai_used": ai_metadata["ai_used"],
        "ai_provider": ai_metadata["ai_provider"],
        "ai_model": ai_metadata["ai_model"],
        "ai_error": ai_metadata["ai_error"],
    }
