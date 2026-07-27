# PO_MONITOR_MAIN

SAP PO 서버·채널·메시지·장애·Collector를 통합 운영하는 내부 모니터링 프로젝트다. 코드는 `frontend`와 `backend`로 완전히 분리하며, AI와 개발자는 작업 전 해당 영역과 도메인의 문서를 순서대로 읽는다.

## 처음 읽는 순서

1. `README.md` — 전체 지도와 실행 방법
2. `MANUAL.md` — 생성·수정·오류 기록 규칙
3. `SKILL.md` — AI 작업 순서와 완료 조건
4. `ERROR.md` — 프로젝트 공통 오류 이력
5. 작업 대상의 `<area>/README.md`
6. 작업 대상의 `<area>/src/domains/<domain>/{README,MANUAL,SKILL,ERROR}.md`

## 영역 지도

| 영역 | 역할 | 안내 |
|---|---|---|
| `frontend` | React 화면, 사용자 대시보드, 알림, LLM 검색 UI | `frontend/README.md` |
| `backend` | FastAPI, 인증·권한, SAP PO 연동, PostgreSQL | `backend/README.md` |

## 도메인 지도

| 도메인 | Frontend | Backend | 책임 |
|---|---:|---:|---|
| auth | O | O | 로그인, 세션, 역할 |
| configuration | - | O | `.env`와 서버 registry |
| server | O | configuration 사용 | 서버 선택과 표시 |
| dashboard | O | O | 사용자별 위젯 구성 |
| monitoring | O | O | 통합 상태와 지표 |
| channels | O | O | 채널 상태와 제어 |
| messages | O | O | 메시지 조회·추적 |
| interfaces | O | O | 인터페이스 기준정보 |
| incidents | O | O | 장애 이력과 해결 |
| collectors | O | O | 증분 수집과 checkpoint |
| alerts | O | O | 실시간 알림·확인 처리 |
| llm_search | O | O | 오류 원인 검색 계약 |

## 실행

```powershell
Copy-Item .env.example .env
.\start-backend.bat
.\start-frontend.bat
```

프론트는 `http://localhost:3000`, 백엔드는 `http://localhost:8000`, API 문서는 `http://localhost:8000/docs`를 사용한다. 데모 계정은 `.env`에서 관리한다.

## 서버 추가

`.env`의 `PO_SERVERS_JSON` 배열에 서버를 추가하고 백엔드를 재시작한다. bootstrap API가 공개 가능한 서버 정보만 내려주므로 프론트 선택 목록은 코드 변경 없이 자동 갱신된다.

## 변경 완료 조건

- 구현과 같은 커밋에서 관련 `README/MANUAL/SKILL/ERROR`를 갱신한다.
- `frontend`: `npm run lint`, `npm test`
- `backend`: Python 3.11.7에서 `pytest`
- 새 환경 변수는 `.env.example`에 추가한다.
- 새 DB 구조는 순번 migration으로 추가한다.
