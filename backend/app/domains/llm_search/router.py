from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.security import require_permissions


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
    return {
        "data": {
            "status": "placeholder",
            "alert_id": request.alert_id,
            "answer": (
                "LLM 연결 전 준비 응답입니다. 실제 연동 단계에서는 선택한 장애 문맥, "
                "도메인 MANUAL.md와 ERROR.md, 과거 해결 이력을 검색해 확인 순서를 제안합니다."
            ),
            "sources": [],
        }
    }
