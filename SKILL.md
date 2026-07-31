# PO_MONITOR_MAIN AI 작업 절차와 도메인 색인

상세 공통 규칙은 `AGENTS.md`가 기준이다. 이 문서는 작업 순서와 관련 도메인 문서 위치를 빠르게 찾기 위한 색인이다.

## 시작

1. `AGENTS.md`, `PROJECT.md`, `CURRENT_TASK.md`를 읽는다.
2. 요청을 frontend/backend와 주·영향 도메인으로 분류한다.
3. 작업 유형에 필요한 루트 문서만 추가로 읽는다.
4. 대상 영역 문서와 대상 도메인의 `README/MANUAL/SKILL/ERROR/API`를 읽는다.
5. 기존 public API, 환경 변수, DB migration과 테스트를 확인한다.

## 작업 원칙

- 관련 없는 도메인을 함께 수정하지 않는다.
- UI 권한 숨김만 믿지 않고 backend permission과 서버 범위를 검증한다.
- SAP·RTIMS·DB·LLM URL과 인증정보를 frontend 응답에 포함하지 않는다.
- LLM에는 마스킹된 장애 문맥만 전달한다.
- 추정으로 API를 만들지 말고 확인된 계약을 `API.md`에 기록한다.
- 코드가 항상 최신이라고 가정하지 않고 테스트·변경 이력·문서를 함께 확인한다.

## 도메인 색인

| 도메인 | 책임 | Frontend | Backend |
|---|---|---|---|
| alerts | 알림·확인 | [`README`](frontend/src/domains/alerts/README.md) | [`README`](backend/app/domains/alerts/README.md) |
| auth | 로그인·세션·역할 | [`README`](frontend/src/domains/auth/README.md) | [`README`](backend/app/domains/auth/README.md) |
| channels | 채널 조회·제어·대량 작업 | [`README`](frontend/src/domains/channels/README.md) | [`README`](backend/app/domains/channels/README.md) |
| collectors | checkpoint·증분 수집 | [`README`](frontend/src/domains/collectors/README.md) | [`README`](backend/app/domains/collectors/README.md) |
| configuration | 서버 registry·연결 준비 상태 | [`server`](frontend/src/domains/server/README.md), [`settings`](frontend/src/domains/settings/README.md) | [`README`](backend/app/domains/configuration/README.md) |
| dashboard | widget·즐겨찾기·요약 | [`README`](frontend/src/domains/dashboard/README.md) | [`README`](backend/app/domains/dashboard/README.md) |
| hrd | HRD 조회·Excel·테스트 | [`README`](frontend/src/domains/hrd/README.md) | [`README`](backend/app/domains/hrd/README.md) |
| incidents | 장애 조회·처리 | [`README`](frontend/src/domains/incidents/README.md) | [`README`](backend/app/domains/incidents/README.md) |
| interfaces | 시스템·Namespace·topology | [`README`](frontend/src/domains/interfaces/README.md) | [`README`](backend/app/domains/interfaces/README.md) |
| llm_search | 마스킹된 JSON 분석 | [`README`](frontend/src/domains/llm_search/README.md) | [`README`](backend/app/domains/llm_search/README.md) |
| messages | 메시지·Message ID·CC 로그 | [`README`](frontend/src/domains/messages/README.md) | [`README`](backend/app/domains/messages/README.md) |
| monitoring | 트래픽·리소스·Queue | [`README`](frontend/src/domains/monitoring/README.md) | [`README`](backend/app/domains/monitoring/README.md) |
| oracle_ifs | Oracle IFS 동기화 | [`README`](frontend/src/domains/oracle_ifs/README.md) | [`README`](backend/app/domains/oracle_ifs/README.md) |
| posts | 운영 지식 게시글 | [`README`](frontend/src/domains/posts/README.md) | [`README`](backend/app/domains/posts/README.md) |
| workspaces | 사용자 작업·단계 진행 | [`README`](frontend/src/domains/workspaces/README.md) | [`README`](backend/app/domains/workspaces/README.md) |

SAP PO와 RTIMS adapter 작업은 각각 `backend/app/integrations/sap_po`, `backend/app/integrations/rtims`의 문서를 추가로 읽는다.

## 완료

- 요청과 직접 검증 가능한 완료 조건을 충족한다.
- 코드·테스트·문서가 같은 책임과 공개 계약을 따른다.
- 관련 `README/MANUAL/SKILL/ERROR/API`와 필요 시 `PROJECT/ROADMAP/CHANGELOG/ADR`를 갱신한다.
- `python scripts\validate_project_docs.py`와 영향 범위 테스트를 실행한다.
- 실제 검증 결과와 미검증 항목을 구분해 보고한다.
