# LLM Search API

`POST /api/v1/llm-search/analyze`는 `llm-search:read` 권한으로 마스킹된 장애 문맥과 질문을 받는다. `LLM_API_URL`이 설정되면 아래 JSON을 해당 주소로 POST한다.

```json
{
  "request_id": "alert-id",
  "task": "incident_analysis",
  "question": "사용자 질문",
  "context": {
    "sid": "POP",
    "title": "오류 제목",
    "detail": "마스킹된 오류 설명",
    "domain": "channels",
    "severity": "critical",
    "status": "open"
  },
  "response_format": {
    "type": "json",
    "schema": {
      "answer": "string",
      "sources": [{"title": "string", "reference": "string"}],
      "confidence": "low|medium|high"
    }
  }
}
```

Provider는 HTTP 2xx와 `{"answer":"...", "sources":[], "confidence":"medium"}` 형식의 JSON 객체를 반환해야 한다. 연결·HTTP·JSON·필수 필드 오류는 `502`다. 설정이 없으면 `status=not_configured`, `response_format=json` 안내 응답을 반환한다.
