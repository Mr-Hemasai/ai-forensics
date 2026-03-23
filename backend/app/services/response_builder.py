from __future__ import annotations

from typing import Any


def _pick_top_entity(structured_result: dict[str, Any]) -> dict[str, Any] | None:
    for key in ["top_entities", "frequency_snapshot", "common_entities", "cross_dataset_snapshot", "outlier_snapshot"]:
        items = structured_result.get(key, [])
        if items:
            return items[0]
    return None


def _default_suggestions(intent: str, case_profile: dict[str, Any]) -> list[str]:
    suggestions = list(case_profile.get("suggestions", []))
    intent_followups = {
        "frequency": ["Show related contacts", "Analyze time pattern for the top entity"],
        "time": ["Find suspicious late-night entities", "Show repeated interactions during peak hours"],
        "relationship": ["Which entity appears across datasets?", "Show suspicious numbers"],
        "cross_dataset": ["Trace the top shared entity", "Show frequency of shared entities"],
        "anomaly": ["Show top entities", "Show flagged entities across datasets"],
    }
    suggestions.extend(intent_followups.get(intent, ["Find suspicious activity", "Find common entities across datasets"]))

    unique: list[str] = []
    for suggestion in suggestions:
        if suggestion not in unique:
            unique.append(suggestion)
    return unique[:6]


def build_response_card(
    intent: str,
    user_message: str,
    structured_result: dict[str, Any],
    case_profile: dict[str, Any],
    focus_entity: str | None = None,
) -> dict[str, Any]:
    override = structured_result.get("response_override")
    if override:
        return {
            "title": override.get("title", "Case Analysis"),
            "direct_answer": override.get("direct_answer", "The requested analysis was completed."),
            "supporting_data": override.get("supporting_data", [])[:8],
            "analysis": override.get("analysis", "The result is based on computed case data."),
            "insight": override.get("insight", "Review the matched records for the next investigation step."),
            "recommended_action": override.get("recommended_action", "Review the supporting records."),
            "leads": structured_result.get("leads", [])[:5],
            "alerts": structured_result.get("alerts", [])[:5],
            "suggestions": override.get("suggestions", _default_suggestions(intent, case_profile)),
            "focus_entity": override.get("focus_entity", focus_entity or (_pick_top_entity(structured_result) or {}).get("value")),
        }

    title = "Case Overview"
    direct_answer = "The uploaded case data has been processed."
    supporting_data: list[str] = []
    analysis = "The system compared the available values across the uploaded datasets."
    insight = "Use the strongest repeated values as the first investigation focus."
    recommended_action = "Review the strongest repeated entities first."

    if intent == "frequency" and structured_result.get("top_entities"):
        top = structured_result["top_entities"][0]
        title = f"Most Active Entity: {top['value']}"
        direct_answer = f"{top['value']} has the highest activity with {top['count']} records."
        supporting_data = [f"{item['value']}: {item['count']} records" for item in structured_result["top_entities"][:5]]
        if len(structured_result["top_entities"]) > 1:
            next_item = structured_result["top_entities"][1]
            difference = top["count"] - next_item["count"]
            analysis = (
                f"This entity has {difference} more records than the next highest entity, {next_item['value']} ({next_item['count']})."
            )
        else:
            analysis = "No other entity in the current result exceeds this count."
        insight = f"{top['value']} is central in the current activity pattern."
        recommended_action = f"Analyze related entities linked to {top['value']} and compare them across datasets."
    elif intent == "time" and structured_result.get("entity") and structured_result.get("total_hits") is not None:
        entity_value = structured_result["entity"]
        title = f"Night Activity: {entity_value}"
        direct_answer = (
            f"{entity_value} appears in {structured_result['night_hits']} night records out of {structured_result['total_hits']} timed records."
        )
        supporting_data = [
            f"Night ratio: {structured_result['night_ratio']}%",
            f"Peak hour: {structured_result['peak_hour']:02d}:00 ({structured_result['peak_hour_count']} records)"
            if structured_result.get("peak_hour") is not None
            else "Peak hour: no valid timestamp found",
        ]
        supporting_data.extend(
            [f"{item['file_name']}: {item['night_hits']} night records" for item in structured_result.get("dataset_breakdown", [])[:3]]
        )
        analysis = (
            f"{entity_value} has {structured_result['night_ratio']}% of its timed activity during night hours."
            if structured_result["total_hits"]
            else f"No valid timed records were found for {entity_value}."
        )
        insight = f"{entity_value} shows a clear time pattern based on the matched case records."
        recommended_action = f"Review the linked contacts of {entity_value} during the peak hour window."
    elif intent == "time" and structured_result.get("time_patterns"):
        top = sorted(structured_result["time_patterns"], key=lambda item: item["night_activity_ratio"], reverse=True)[0]
        title = f"Late-Night Activity: {top['file_name']}"
        direct_answer = f"{top['file_name']} has {top['night_activity_count']} night records, which is {top['night_activity_ratio']}% of the timed data."
        supporting_data = [f"Peak hour: {top['peak_hour']:02d}:00 ({top['peak_hour_count']} records)"]
        supporting_data.extend([f"{item['value']}: {item['count']} night records" for item in top["night_entities"][:3]])
        analysis = f"The peak hour is {top['peak_hour']:02d}:00 with {top['peak_hour_count']} records."
        if top["night_entities"]:
            analysis += " Top night entities: " + ", ".join(f"{item['value']} ({item['count']})" for item in top["night_entities"][:3])
        insight = f"{top['file_name']} has concentrated activity during late hours."
        recommended_action = "Open the timeline and review the entities active in the peak hour."
    elif intent == "relationship" and structured_result.get("entity") and not structured_result.get("contact_ranking"):
        entity_value = structured_result["entity"]
        direction = structured_result.get("relationship_direction", "outgoing")
        title = f"No {'Outgoing' if direction == 'outgoing' else 'Incoming'} Contact Match"
        direct_answer = (
            f"No outgoing contact records were found for {entity_value}."
            if direction == "outgoing"
            else f"No incoming contact records were found for {entity_value}."
        )
        analysis = (
            f"The relationship search did not find rows where {entity_value} appears as the caller."
            if direction == "outgoing"
            else f"The relationship search did not find rows where {entity_value} appears as the receiver."
        )
        insight = f"{entity_value} is not present in the matching relationship direction in the loaded data."
        recommended_action = "Check the entity value or run a broader frequency query first."
    elif intent == "relationship" and structured_result.get("contact_ranking"):
        entity_value = structured_result["entity"]
        direction = structured_result.get("relationship_direction", "outgoing")
        top = structured_result["contact_ranking"][0]
        title = (
            f"Top Contacted Entity: {top['value']}"
            if direction == "outgoing"
            else f"Top Incoming Contact: {top['value']}"
        )
        direct_answer = (
            f"{entity_value} called {top['value']} {top['count']} times."
            if direction == "outgoing"
            else f"{top['value']} contacted {entity_value} {top['count']} times."
        )
        supporting_data = [f"{item['value']}: {item['count']} interactions" for item in structured_result["contact_ranking"][:5]]
        if len(structured_result["contact_ranking"]) > 1:
            next_item = structured_result["contact_ranking"][1]
            difference = top["count"] - next_item["count"]
            analysis = (
                f"{top['value']} ranks first with {difference} more interactions than {next_item['value']} ({next_item['count']})."
            )
        else:
            analysis = "No second contact in the current result exceeds this interaction count."
        insight = (
            f"{top['value']} is the strongest outgoing contact for {entity_value}."
            if direction == "outgoing"
            else f"{top['value']} is the strongest incoming contact for {entity_value}."
        )
        recommended_action = f"Trace both {entity_value} and {top['value']} across the other datasets."
    elif intent == "relationship" and structured_result.get("relationships"):
        relation = next((item for item in structured_result["relationships"] if item["pairs"]), None)
        if relation:
            top = relation["pairs"][0]
            title = f"Top Relationship: {top['source']} ↔ {top['target']}"
            direct_answer = f"{top['source']} and {top['target']} are the strongest repeated pair with {top['count']} interactions."
            supporting_data = [f"{item['source']} ↔ {item['target']}: {item['count']}" for item in relation["pairs"][:5]]
            if len(relation["pairs"]) > 1:
                analysis = "This pair ranks above the other visible pairs in the same dataset."
            else:
                analysis = "No other pair in the current result exceeds this interaction count."
            insight = f"{top['source']} and {top['target']} form a key connection pair in this case."
            recommended_action = f"Trace both entities across the other datasets and inspect their timelines."
    elif intent == "cross_dataset" and structured_result.get("common_entities"):
        top = structured_result["common_entities"][0]
        title = f"Cross-Dataset Match: {top['value']}"
        direct_answer = f"{top['value']} appears in {top['file_count']} datasets."
        supporting_data = [f"{item['value']}: {item['file_count']} datasets" for item in structured_result["common_entities"][:5]]
        if len(structured_result["common_entities"]) > 1:
            analysis = "This entity has wider dataset presence than the next visible shared entities."
        else:
            analysis = "No other shared entity in the current result appears in more datasets."
        insight = f"{top['value']} is a strong cross-dataset anchor in this case."
        recommended_action = f"Trace {top['value']} across all matched files and review linked entities."
    elif intent == "anomaly":
        snapshot = _pick_top_entity(structured_result)
        title = "Suspicious Pattern Scan"
        if snapshot and snapshot.get("value"):
            direct_answer = f"{snapshot['value']} is the top flagged entity in the suspicious pattern scan."
        else:
            direct_answer = "The suspicious pattern scan found flagged entities in the current case."
        supporting_data = structured_result.get("alerts", [])[:5]
        if structured_result.get("alerts"):
            analysis = "The same entity or pattern was flagged by multiple computed checks."
        else:
            analysis = "The suspicious scan used high frequency, night activity, repeated links, and cross-dataset presence."
        insight = "Entities named in the alerts are the strongest current risk points."
        recommended_action = "Review the top flagged entity, then compare it with timeline and cross-dataset matches."
    elif intent == "entity_profile" and focus_entity:
        title = f"Entity Trace: {focus_entity}"
        direct_answer = f"The follow-up query is focused on {focus_entity}."
        analysis = "The system reused the last confirmed focus entity from the current case chat context."
        insight = f"{focus_entity} remains the active investigation target in this follow-up step."
        recommended_action = f"Check the timeline and linked entities for {focus_entity}."

    return {
        "title": title,
        "direct_answer": direct_answer,
        "supporting_data": supporting_data,
        "analysis": analysis,
        "insight": insight,
        "recommended_action": recommended_action,
        "leads": structured_result.get("leads", [])[:5],
        "alerts": structured_result.get("alerts", [])[:5],
        "suggestions": _default_suggestions(intent, case_profile),
        "focus_entity": focus_entity or (_pick_top_entity(structured_result) or {}).get("value"),
    }


def response_card_to_text(card: dict[str, Any]) -> str:
    lines = [card["title"], "", f"Direct Answer: {card['direct_answer']}"]

    if card.get("context_used"):
        lines.extend(["", f"Context Used: {card['context_used']}"])

    if card.get("supporting_data"):
        lines.append("")
        lines.append("Supporting Data:")
        lines.extend([f"- {item}" for item in card["supporting_data"][:5]])

    lines.extend(["", f"Analysis: {card['analysis']}", "", f"Insight: {card['insight']}", "", f"Recommended Action: {card['recommended_action']}"])

    for lead in card.get("leads", [])[:3]:
        lines.append(f"[LEAD] {lead}")
    for alert in card.get("alerts", [])[:3]:
        lines.append(f"[ALERT] {alert}")

    return "\n".join(lines)


def extract_observation_points(card: dict[str, Any], structured_result: dict[str, Any]) -> list[str]:
    items: list[str] = []
    if card.get("direct_answer"):
        items.append(card["direct_answer"])
    if card.get("supporting_data"):
        items.extend(card["supporting_data"][:2])
    items.extend(structured_result.get("alerts", [])[:2])
    items.extend(structured_result.get("leads", [])[:2])

    unique: list[str] = []
    for item in items:
        if item and item not in unique:
            unique.append(item)
    return unique[:6]
