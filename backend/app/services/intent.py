from __future__ import annotations

import re
from datetime import datetime
from typing import Any


PHONE_RE = re.compile(r"\b\d{7,15}\b")
IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
ID_RE = re.compile(r"\b\d{14,16}\b")
MONTH_WINDOW_RE = re.compile(
    r"(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:t|tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+(\d{1,2})(?:\s*[-–]\s*(\d{1,2}))?(?:,\s*(\d{4}))?",
    re.IGNORECASE,
)
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

FOLLOW_UP_REFERENCES = {
    "their",
    "them",
    "same",
    "that number",
    "this number",
    "that entity",
    "this entity",
    "show more",
    "what about",
    "to whom",
}

INTENT_KEYWORDS: dict[str, list[str]] = {
    "frequency": ["top", "most", "active", "highest", "frequent", "made the most", "most calls"],
    "time": ["night", "late", "hour", "time", "midnight", "evening"],
    "relationship": ["connect", "contact", "link", "relationship", "called", "contacted", "to whom", "who contacted"],
    "cross_dataset": ["common", "across", "everywhere", "shared", "overlap", "multiple datasets", "join", "merge"],
    "anomaly": ["suspicious", "anomaly", "risk", "alert", "unusual", "outlier", "fraud"],
}
INTENT_PRIORITY = ["relationship", "cross_dataset", "anomaly", "time", "frequency", "overview"]


def extract_entities(message: str) -> list[str]:
    found: list[str] = []
    for pattern in (IP_RE, ID_RE, PHONE_RE):
        for match in pattern.findall(message):
            if match not in found:
                found.append(match)
    return found


def extract_date_window(message: str) -> dict[str, int | None] | None:
    match = MONTH_WINDOW_RE.search(message.replace("–", "-"))
    if not match:
        return None
    month_token = match.group(1).lower()
    return {
        "month": MONTH_MAP[month_token],
        "start_day": int(match.group(2)),
        "end_day": int(match.group(3) or match.group(2)),
        "year": int(match.group(4)) if match.group(4) else None,
    }


def _uses_context_reference(text: str) -> bool:
    phrase_tokens = {"that number", "this number", "that entity", "this entity", "show more", "what about", "to whom"}
    for token in phrase_tokens:
        if token in text:
            return True
    for token in FOLLOW_UP_REFERENCES - phrase_tokens:
        if re.search(rf"\b{re.escape(token)}\b", text):
            return True
    return False


def detect_intent(message: str, case_context: dict[str, Any] | None = None) -> dict[str, Any]:
    text = message.lower().strip()
    case_context = case_context or {}
    extracted_entities = extract_entities(message)
    explicit_entity = extracted_entities[0] if extracted_entities else None
    date_window = extract_date_window(message)
    uses_context_reference = _uses_context_reference(text)
    used_context = False
    burner_requested = "burner" in text

    intent = "overview"
    query_type = "overview"
    relationship_direction: str | None = None
    requires_entity = False

    if "show more" in text and case_context.get("last_query_type"):
        intent = case_context.get("last_intent", "overview")
        query_type = case_context["last_query_type"]
    elif "final investigative summary" in text or "who should be arrested first" in text or "strongest evidence" in text:
        intent = "investigation"
        query_type = "final_action_summary"
    elif "leader of the network" in text or "most likely the leader" in text or "hierarchy" in text:
        intent = "investigation"
        query_type = "hierarchy_inference"
    elif "counter-surveillance" in text or "avoid detection" in text:
        intent = "investigation"
        query_type = "counter_surveillance"
    elif "complete profile" in text or "using all three datasets" in text:
        intent = "cross_dataset"
        query_type = "entity_profile"
        requires_entity = not burner_requested
    elif "critical window" in text or "reconstruct a timeline" in text or "timeline of events" in text:
        intent = "cross_dataset"
        query_type = "critical_window"
    elif "vpn" in text:
        intent = "ipdr"
        query_type = "vpn_usage"
    elif "tor" in text or "dark web" in text:
        intent = "ipdr"
        query_type = "tor_usage"
    elif "trace ip activity" in text or ("ip activity" in text and "across" in text):
        intent = "ipdr"
        query_type = "cross_dataset_ip_activity"
    elif "encrypted messaging" in text or "whatsapp" in text or "telegram" in text or "signal" in text:
        intent = "ipdr"
        query_type = "encrypted_apps"
    elif "suspicious external ip" in text or "suspicious ip" in text:
        intent = "ipdr"
        query_type = "suspicious_ips"
    elif "upload" in text or "download anomaly" in text or "data upload" in text:
        intent = "ipdr"
        query_type = "upload_download_anomalies"
    elif "internet activity profile" in text and burner_requested:
        intent = "ipdr"
        query_type = "burner_ipdr_profile"
    elif "highest number of hits" in text or "highest hits" in text:
        intent = "tower"
        query_type = "tower_top_hits"
    elif "same tower" in text or "co-location" in text or "co located" in text or "co-location events" in text:
        intent = "tower"
        query_type = "tower_colocation"
        requires_entity = len(extracted_entities) < 2 and not burner_requested
    elif "physical movement" in text or "movement across" in text or ("track" in text and "tower" in text):
        intent = "tower"
        query_type = "tower_movement"
        requires_entity = not burner_requested
    elif "widest geographic spread" in text or "geographic spread" in text:
        intent = "tower"
        query_type = "tower_spread"
    elif "who called" in text and explicit_entity:
        intent = "cdr"
        query_type = "calls_to_entity"
        relationship_direction = "incoming"
        requires_entity = True
    elif "top phone number" in text or "top phone numbers" in text or ("phone numbers" in text and any(token in text for token in ["top", "most", "active", "highest"])):
        intent = "frequency"
        query_type = "top_phone_numbers"
    elif "most calls overall" in text or "call frequency" in text or "made the most calls" in text:
        intent = "cdr"
        query_type = "cdr_top_callers"
    elif "calls between" in text and len(extracted_entities) >= 2:
        intent = "cdr"
        query_type = "cdr_pair_history_night" if any(token in text for token in ["night", "late", "midnight"]) else "cdr_pair_history"
    elif "night" in text and "call" in text:
        intent = "cdr"
        query_type = "cdr_night_calls"
    elif ("calls made between" in text and ("pm" in text or "am" in text)) or "night-time communication" in text:
        intent = "cdr"
        query_type = "cdr_night_calls"
    elif "day-by-day" in text or "weekly pattern" in text or "weekday pattern" in text:
        intent = "cdr"
        query_type = "cdr_day_week_patterns"
        requires_entity = not explicit_entity and len(extracted_entities) < 2
    elif burner_requested and ("role" in text or "entire call activity" in text):
        intent = "cdr"
        query_type = "burner_cdr_profile"
    elif any(keyword in text for keyword in INTENT_KEYWORDS["cross_dataset"]):
        intent = "cross_dataset"
        query_type = "common_entities"
    elif any(keyword in text for keyword in INTENT_KEYWORDS["anomaly"]):
        intent = "anomaly"
        query_type = "suspicious_patterns"
    elif (
        "to whom" in text
        or "whom" in text
        or "who did" in text
        or "called the most" in text
        or "outgoing" in text
        or "called most" in text
    ):
        intent = "relationship"
        query_type = "outgoing_calls"
        relationship_direction = "outgoing"
        requires_entity = True
    elif "who contacted" in text or "who called" in text or "incoming" in text or "from whom" in text:
        intent = "relationship"
        query_type = "incoming_calls"
        relationship_direction = "incoming"
        requires_entity = True
    elif any(keyword in text for keyword in INTENT_KEYWORDS["relationship"]):
        intent = "relationship"
        query_type = "relationship_summary"
    elif any(keyword in text for keyword in INTENT_KEYWORDS["time"]):
        intent = "time"
        query_type = "night_activity" if any(token in text for token in ["night", "late", "midnight"]) else "time_activity"
        requires_entity = any(token in text for token in ["their", "them", "that", "this number", "that number"])
    elif any(keyword in text for keyword in INTENT_KEYWORDS["frequency"]):
        intent = "frequency"
        query_type = "top_entities"
    else:
        scores = {name: 0 for name in INTENT_KEYWORDS}
        for name, keywords in INTENT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    scores[name] += 1
        best_score = max(scores.values()) if scores else 0
        if best_score > 0:
            candidates = [name for name, score in scores.items() if score == best_score]
            intent = next((name for name in INTENT_PRIORITY if name in candidates), "overview")
            query_type = "general_follow_up" if intent == "overview" else f"{intent}_follow_up"

    resolved_entity = explicit_entity
    if not resolved_entity and (requires_entity or uses_context_reference or query_type == "general_follow_up"):
        resolved_entity = case_context.get("last_entity")
        used_context = bool(resolved_entity)

    if intent == "time" and not explicit_entity and case_context.get("last_entity") and uses_context_reference:
        resolved_entity = case_context["last_entity"]
        used_context = True
        requires_entity = True

    if intent == "relationship" and query_type in {"outgoing_calls", "incoming_calls"} and not resolved_entity:
        requires_entity = True

    return {
        "intent": intent,
        "query_type": query_type,
        "entity": resolved_entity,
        "entities": extracted_entities,
        "explicit_entity": explicit_entity,
        "date_window": date_window,
        "relationship_direction": relationship_direction,
        "requires_entity": requires_entity,
        "used_context": used_context,
        "is_follow_up": uses_context_reference or used_context or "show more" in text,
        "burner_requested": burner_requested,
        "night_filter": any(token in text for token in ["night", "late", "midnight"]),
    }
