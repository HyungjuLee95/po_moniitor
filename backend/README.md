# Backend

Python 3.11.7/FastAPI/PostgreSQL 기반 API다. `app/core`는 환경·보안, `app/domains`는 업무 기능, `migrations`는 순차 DB 변경을 담당한다.

도메인은 `auth`, `configuration`, `dashboard`, `monitoring`, `channels`, `messages`, `interfaces`, `incidents`, `collectors`, `alerts`, `llm_search`로 구성한다. API prefix는 `/api/v1`이다.

실제 SAP PO 호출 구현 전 각 도메인의 MANUAL에서 endpoint와 timeout, 마스킹, 오류 변환 규칙을 확인한다.
