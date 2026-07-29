# LLM Search API

장애 분석은 `POST /llm-search/analyze`에 `alert_id`, `question`, 마스킹 대상 `context` JSON을 보낸다. 응답의 `data.answer`를 표시하며 `status`는 `completed` 또는 `not_configured`, `response_format`은 `json`이다. Provider URL은 frontend에 노출하지 않는다.
