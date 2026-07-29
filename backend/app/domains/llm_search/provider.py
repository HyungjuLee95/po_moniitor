from __future__ import annotations

from typing import Any

import requests

from app.core.config import settings


class LlmProviderError(RuntimeError):
    """Sanitized LLM provider error."""


_ALLOWED_CONTEXT_KEYS = {
    "id",
    "sid",
    "title",
    "detail",
    "domain",
    "severity",
    "status",
    "occurredAt",
    "occurred_at",
}


def sanitize_context(context: dict[str, Any]) -> dict[str, str]:
    return {
        key: str(value)[:2000]
        for key, value in context.items()
        if key in _ALLOWED_CONTEXT_KEYS and value is not None
    }


class JsonLlmProvider:
    def analyze(
        self,
        alert_id: str,
        question: str,
        context: dict[str, Any],
    ) -> dict:
        request_payload = {
            "request_id": alert_id,
            "task": "incident_analysis",
            "question": question,
            "context": sanitize_context(context),
            "response_format": {
                "type": "json",
                "schema": {
                    "answer": "string",
                    "sources": [
                        {"title": "string", "reference": "string"}
                    ],
                    "confidence": "low|medium|high",
                },
            },
        }
        try:
            response = requests.post(
                settings.llm_api_url,
                json=request_payload,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                timeout=settings.llm_api_timeout_seconds,
            )
            response.raise_for_status()
            result = response.json()
        except (requests.RequestException, ValueError) as exc:
            raise LlmProviderError("LLM JSON API request failed") from exc

        if not isinstance(result, dict):
            raise LlmProviderError("LLM JSON API returned an invalid object")
        answer = result.get("answer")
        if not isinstance(answer, str) or not answer.strip():
            raise LlmProviderError("LLM JSON API response is missing answer")
        sources = result.get("sources", [])
        if not isinstance(sources, list):
            raise LlmProviderError("LLM JSON API response has invalid sources")
        safe_sources = [
            {
                "title": str(item.get("title") or "")[:200],
                "reference": str(item.get("reference") or "")[:500],
            }
            for item in sources
            if isinstance(item, dict)
        ]
        confidence = str(result.get("confidence") or "unknown").lower()
        if confidence not in {"low", "medium", "high"}:
            confidence = "unknown"
        return {
            "status": "completed",
            "alert_id": alert_id,
            "answer": answer.strip(),
            "sources": safe_sources,
            "confidence": confidence,
            "response_format": "json",
        }
