from __future__ import annotations

import json
import os
from typing import Any

from openai import OpenAI


def _resolve_client() -> tuple[OpenAI | None, str, str]:
    api_key = os.getenv("AI_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return None, "", "none"

    base_url = os.getenv("AI_BASE_URL")
    if not base_url and api_key.startswith("sk-or-v1"):
        base_url = "https://openrouter.ai/api/v1"

    model = os.getenv("AI_MODEL")
    if not model:
        model = "gpt-4.1-mini" if not base_url else "openrouter/free"

    client = OpenAI(api_key=api_key, base_url=base_url or None)
    provider = "openrouter" if (base_url and "openrouter.ai" in base_url) or api_key.startswith("sk-or-v1") else "openai"
    return client, model, provider


def enhance_response_card(
    card: dict[str, Any], intent: str, user_message: str, structured_result: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    client, model, provider = _resolve_client()
    if not client:
        metadata = {
            "ai_used": False,
            "ai_provider": provider,
            "ai_model": model or None,
            "ai_error": "AI_API_KEY is not configured on the backend.",
        }
        card.update(metadata)
        return card, metadata

    try:
        prompt = f"""
You are formatting a forensic analysis result.
Do not change facts.
Use simple English.
Avoid generic AI language.
Avoid vague phrases such as "may indicate", "could suggest", "might be", or "appears to".
Every sentence must be grounded in the computed data already provided.
Return valid JSON with keys: direct_answer, analysis, insight, recommended_action.

Intent: {intent}
User message: {user_message}
Current card:
{json.dumps(card, default=str)}

Structured result:
{json.dumps(structured_result, default=str)}
"""
        response = client.chat.completions.create(
            model=model,
            temperature=0.2,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Rewrite forensic response sections only. "
                        "Keep them factual, simple, and investigation-oriented. "
                        "Do not add new facts."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content or "{}"
        parsed = json.loads(content)
        for key in ["direct_answer", "analysis", "insight", "recommended_action"]:
            if isinstance(parsed.get(key), str) and parsed[key].strip():
                card[key] = parsed[key].strip()
        metadata = {"ai_used": True, "ai_provider": provider, "ai_model": model, "ai_error": None}
        card.update(metadata)
        return card, metadata
    except Exception as exc:
        metadata = {
            "ai_used": False,
            "ai_provider": provider,
            "ai_model": model or None,
            "ai_error": f"{type(exc).__name__}: {exc}",
        }
        card.update(metadata)
        return card, metadata
