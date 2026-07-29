from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.security import require_permissions
from app.core.config import settings
from app.domains.llm_search.provider import JsonLlmProvider, LlmProviderError


class AnalysisRequest(BaseModel):
    alert_id: str = Field(min_length=1, max_length=128)
    question: str = Field(min_length=3, max_length=2000)
    context: dict[str, Any] = Field(default_factory=dict)


router = APIRouter(prefix="/llm-search", tags=["LLM Search"])


@router.post("/analyze")
def analyze(
    request: AnalysisRequest,
    _: dict = Depends(require_permissions("llm-search:read")),
) -> dict:
    if settings.llm_api_url:
        try:
            return {
                "data": JsonLlmProvider().analyze(
                    request.alert_id,
                    request.question,
                    request.context,
                )
            }
        except LlmProviderError as exc:
            raise HTTPException(
                status_code=502,
                detail="LLM JSON API request failed",
            ) from exc
    return {
        "data": {
            "status": "not_configured",
            "alert_id": request.alert_id,
            "answer": (
                "LLM_API_URL이 설정되지 않았습니다. .env에 JSON API 주소를 "
                "설정하고 백엔드를 재시작해 주세요."
            ),
            "sources": [],
            "confidence": "unknown",
            "response_format": "json",
        }
    }
