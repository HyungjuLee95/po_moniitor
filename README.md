# PO_MONITOR_MAIN

로컬 `DEMO_MODE=true`의 초기 계정은 `admin / 1234` 하나만 제공한다. 운영 환경에서는 `DEMO_MODE=false`와 PostgreSQL 사용자 계정을 사용한다.

SAP PO 서버·채널·메시지·장애·Collector를 통합 운영하는 내부 모니터링 프로젝트다. 프론트는 공식 Next.js 16.2.12 App Router와 React 19.2.7, 백엔드는 Python 3.11.7과 FastAPI를 사용한다. 코드는 `frontend`와 `backend`로 완전히 분리하며, AI와 개발자는 작업 전 해당 영역과 도메인의 문서를 순서대로 읽는다.

## 처음 읽는 순서

1. `AGENTS.md` — AI 작업·보안·검증 규칙
2. `PROJECT.md` — 목표·제약·전체 도메인 지도
3. `CURRENT_TASK.md` — 현재 작업의 읽기·변경·검증 범위
4. 작업 유형에 필요한 `MANUAL.md`, `ERROR.md`, `docs/*`
5. 대상 영역의 `README.md`, `MANUAL.md`, `SKILL.md`, `ERROR.md`
6. 대상 도메인의 `README.md`, `MANUAL.md`, `SKILL.md`, `ERROR.md`, `API.md`

## 주요 문서

| 문서 | 용도 |
|---|---|
| [`PROJECT.md`](PROJECT.md) | 프로젝트 목표, 공통 제약, 전체 영역·도메인 지도 |
| [`CURRENT_TASK.md`](CURRENT_TASK.md) | 현재 작업 범위와 완료 조건, AI 읽기 범위 |
| [`ROADMAP.md`](ROADMAP.md) | 사내 검증과 후속 구현 우선순위 |
| [`MANUAL.md`](MANUAL.md) | 프로젝트 생성·실행·오류·API 문서 규칙 |
| [`SKILL.md`](SKILL.md) | AI 작업 순서와 도메인 색인 |
| [`ERROR.md`](ERROR.md) | 공통 오류와 재발 방지 지식 |
| [`CHANGELOG.md`](CHANGELOG.md) | 사용자·운영·개발 절차 영향 변경 |
| [`docs/`](docs/) | 요구사항, 아키텍처, 테스트, 품질, 배포, ADR |

## 영역 지도

| 영역 | 역할 | 안내 |
|---|---|---|
| `frontend` | React 화면, 사용자 대시보드, 알림, LLM 검색 UI | `frontend/README.md` |
| `backend` | FastAPI, 인증·권한, SAP PO 연동, PostgreSQL | `backend/README.md` |

기존 프로젝트 분석 자료와 현재 이식 상태의 차이는
[`docs/LEGACY_FEATURE_COVERAGE.md`](docs/LEGACY_FEATURE_COVERAGE.md)를 기준으로 확인한다.
사내망 설치 파일과 `pip`/`npm` 인증서·오프라인 설치 절차는
[`docs/INSTALL_INTERNAL_NETWORK.md`](docs/INSTALL_INTERNAL_NETWORK.md)를 따른다.

## 도메인 지도

| 도메인 | Frontend | Backend | 책임 |
|---|---:|---:|---|
| auth | O | O | 로그인, 세션, 역할 |
| configuration | - | O | `.env`와 서버 registry |
| server | O | configuration 사용 | 서버 선택과 표시 |
| dashboard | O | O | 사용자별 위젯 구성·즐겨찾기·사용 빈도 메뉴 |
| monitoring | O | O | 실시간 인터페이스·실제 24시간 트래픽·시스템 처리·Queue |
| channels | O | O | 채널 상태와 제어 |
| messages | O | O | 메시지 조회·추적 |
| interfaces | O | O | 인터페이스 기준정보 |
| incidents | O | O | 장애 이력과 해결 |
| collectors | O | O | 증분 수집과 checkpoint |
| workspaces | O | O | 프로젝트 작업·진행 단계 관리 |
| alerts | O | O | 실시간 알림·확인 처리 |
| llm_search | O | O | 오류 원인 검색 계약 |
| settings | O | configuration/auth/collectors 사용 | 연결·기준·사용자·수집 관리 |
| hrd | O | O | HRD 인터페이스·Excel·테스트 메시지·7일 Delivering 일일 점검 |
| oracle_ifs | O | O | Oracle IFS 동기화·cache·이관 예정일 |
| posts | O | O | 운영 지식 게시글 |

## 실행

### 1. 최초 1회 준비

사내망에서는 `venv`를 사용하지 않는다. `python --version` 결과가 `Python 3.11.7`인지 확인한 뒤 시스템 Python에 백엔드 패키지를 직접 설치한다.

```powershell
cd D:\toyproject\PO_MONITOR_MAIN
Copy-Item .env.example .env

python --version
python -m pip install --upgrade pip
python -m pip install -r backend\requirements.txt

cd frontend
npm install
cd ..
```

### 2. 백엔드 실행 — 터미널 1

```powershell
cd D:\toyproject\PO_MONITOR_MAIN
python -m uvicorn app.main:app --app-dir backend --reload --host 0.0.0.0 --port 8000
```

또는:

```powershell
.\start-backend.bat
```

### 3. 프론트 실행 — 터미널 2

```powershell
cd D:\toyproject\PO_MONITOR_MAIN\frontend
npm run dev
```

위 명령은 공식 Next.js 개발 서버를 실행한다. Vinext/Vite/Cloudflare Worker 호환 런타임은 사용하지 않는다.

또는 프로젝트 루트에서:

```powershell
.\start-frontend.bat
```

### 4. 운영 빌드

```powershell
cd D:\toyproject\PO_MONITOR_MAIN\frontend
npm run build
npm run start
```

프론트는 `http://localhost:3000`, 백엔드는 `http://localhost:8000`, API 문서는 `http://localhost:8000/docs`, 상태 확인은 `http://localhost:8000/health`를 사용한다.

### 5. SAP PO 실데이터 전환

```env
DEMO_MODE=true
SAP_PO_LIVE_MODE=true
SAP_PO_USER=현재 사용 가능한 SAP PO API 계정
SAP_PO_PASSWORD=현재 비밀번호
SAP_VERIFY_TLS=false
```

`DEMO_MODE`는 로그인/DB 모드이고 `SAP_PO_LIVE_MODE`는 SAP 호출 모드다. 처음 사내망에서 확인할 때는 위 조합으로 데모 로그인을 유지하면서 SAP 데이터만 실호출할 수 있다. 운영 계정 DB가 준비되면 `DEMO_MODE=false`로 변경한다.

기존 RTIMS Oracle을 사용할 때는 `.env`의 `RTIMS_ENABLED=true`와 `RTIMS_ORACLE_*` 값을 설정한다. 이 경우 대시보드 통계·최근 메시지·장애는 RTIMS에서 조회하고, 채널 실시간 상태·제어·audit은 SAP PO API를 호출한다. PostgreSQL은 사용자·권한·대시보드 개인 설정용으로 별도 유지한다.

내부 LLM JSON API를 연결할 때는 `.env`의 `LLM_API_URL`에 분석 endpoint 주소를 설정하고 백엔드를 재시작한다. 브라우저는 해당 주소를 직접 호출하지 않으며 `/api/v1/llm-search/analyze`가 중계한다.

### 6. PostgreSQL migration

```powershell
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" `
  -h localhost -p 5432 -U postgres -d po_monitor `
  -f backend\migrations\001_initial.sql

& "C:\Program Files\PostgreSQL\17\bin\psql.exe" `
  -h localhost -p 5432 -U postgres -d po_monitor `
  -f backend\migrations\002_dashboard_alert_llm.sql

& "C:\Program Files\PostgreSQL\17\bin\psql.exe" `
  -h localhost -p 5432 -U postgres -d po_monitor `
  -f backend\migrations\003_workspaces.sql

& "C:\Program Files\PostgreSQL\17\bin\psql.exe" `
  -h localhost -p 5432 -U postgres -d po_monitor `
  -f backend\migrations\004_monitoring_policy_and_iam.sql

& "C:\Program Files\PostgreSQL\17\bin\psql.exe" `
  -h localhost -p 5432 -U postgres -d po_monitor `
  -f backend\migrations\005_required_feature_domains.sql
```

## 서버 추가

`.env`의 `PO_SERVERS_JSON` 배열에 서버를 추가하고 백엔드를 재시작한다. bootstrap API가 공개 가능한 서버 정보만 내려주므로 프론트 선택 목록은 코드 변경 없이 자동 갱신된다.

실제 SAP 서버 주소와 계정은 `.env`에만 작성한다. `.env.example`에는 운영값을 커밋하지 않는다.

연결 점검 API:

```text
GET /api/v1/configuration/sap-po-check?sid=POQ
GET /api/v1/configuration/rtims-check
```

## 변경 완료 조건

- 구현과 같은 커밋에서 관련 `README/MANUAL/SKILL/ERROR/API`를 갱신한다.
- `python scripts\validate_project_docs.py`
- `frontend`: `npm run lint`, `npm test`
- `backend`: Python 3.11.7에서 `pytest`
- 새 환경 변수는 `.env.example`에 추가한다.
- 새 DB 구조는 순번 migration으로 추가한다.
