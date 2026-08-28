# PO_MONITOR_MAIN

로컬 `DEMO_MODE=true`의 초기 계정은 `admin / 1234` Administrator 하나만 제공한다. 나머지 사용자는 로그인 화면에서 가입한 뒤 Administrator가 역할과 접근 서버를 승인한다. 데모 가입 정보는 backend 재시작 시 초기화되며 운영 환경은 `DEMO_MODE=false`와 PostgreSQL 사용자 계정을 사용한다.

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
| certificates | O | O | SAP PO 키스토어 인증서와 만료 상태 |
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

백그라운드 메시지 Collector는 별도 opt-in인 `RTIMS_COLLECTOR_ENABLED=true`로 켠다. 기본값은 `false`이며 활성 `collector` capability 서버와 profile을 순차 실행한다. `PO_SERVERS_JSON[].collectors`가 있으면 HANA `bc_msg/bc_msg_log`의 bounded page를 Oracle `MON_BUF_AAE_MSG -> process_msg_logs`로 처리하고 Oracle checkpoint를 같은 transaction에서 전진한다. profile이 없는 서버만 기존 SAP PO 조회·PostgreSQL checkpoint 호환 경로를 사용한다. PostgreSQL은 사용자·권한·개인 설정의 기본 DB로 유지한다.

새 RTIMS schema가 필요한 환경은 runtime 계정과 별도로 `RTIMS_ORACLE_DDL_USER`, `RTIMS_ORACLE_DDL_PASSWORD`를 설정한 뒤 아래 원클릭 명령을 사용한다. 두 계정이 다르면 `RTIMS_ORACLE_SCHEMA`에 DDL owner 이름을 설정하며, 실행기가 runtime 계정에 14개 객체 SELECT와 장애처리 컬럼 UPDATE 권한을 부여한다. PostgreSQL은 `RTIMS_POSTGRES_DATABASE_URL`을 사용하며, 비어 있으면 기존 `DATABASE_URL`에 `rtims` schema를 만든다. Oracle은 `RTIMS_ORACLE_HOST/PORT/SERVICE`와 DDL 계정을 읽는다. 기존 객체나 데이터는 삭제하지 않으며 현재 backend가 사용하는 14개 객체와 필수 컬럼을 생성·검증한다.

```powershell
# PostgreSQL + Oracle 생성 후 계약 검증
.\scripts\setup-rtims-databases.ps1 -Target all

# 생성 없이 현재 상태만 검증
.\scripts\setup-rtims-databases.ps1 -Target all -CheckOnly

# 한 DB만 적용
.\scripts\setup-rtims-databases.ps1 -Target postgresql
.\scripts\setup-rtims-databases.ps1 -Target oracle
```

Windows에서 `setup-rtims-databases.bat`를 실행해 두 DB를 한 번에 적용할 수도 있다. Oracle 운영 schema가 이미 있다면 먼저 `-CheckOnly`를 실행한다. `MON_DAILY_CLOSE_STAT`은 원본 DDL이 제공되지 않아 현재 조회 컬럼만 반영한 최소 호환 계약이며, Collector 전체 buffer·sequence·procedure schema는 포함하지 않는다. Oracle Collector를 켜려면 기존 전체 RTIMS schema 또는 DBA가 검증한 원본 Collector DDL이 별도로 필요하다.

내부 LLM JSON API를 연결할 때는 `.env`의 `LLM_API_URL`에 분석 endpoint 주소를 설정하고 백엔드를 재시작한다. 브라우저는 해당 주소를 직접 호출하지 않으며 `/api/v1/llm-search/analyze`가 중계한다.

### DB·외부 시스템 접속정보 관리

실제 접속정보의 단일 원본은 프로젝트 루트의 `.env`다. `.env`는 Git에서 제외되며 코드·문서·frontend에는 실제 host, 사용자, 비밀번호를 작성하지 않는다. `.env.example`에는 변수명과 비민감 예시만 유지한다.

| 대상 | `.env` 변수 | 용도와 fallback |
|---|---|---|
| 애플리케이션 PostgreSQL | `DATABASE_URL` | 사용자·권한·대시보드·워크스페이스·게시글 저장 |
| RTIMS 호환 PostgreSQL | `RTIMS_POSTGRES_DATABASE_URL` | 비어 있으면 `DATABASE_URL` 사용 |
| RTIMS Oracle 조회 | `RTIMS_ORACLE_HOST/PORT/SERVICE/SCHEMA/USER/PASSWORD` | 메시지·장애·리소스·Queue 조회 runtime 계정 |
| RTIMS Oracle DDL | `RTIMS_ORACLE_DDL_USER/PASSWORD` | 선택적 schema 생성 전용 계정. runtime 계정과 분리 |
| RTIMS Collector Oracle | `RTIMS_COLLECTOR_ORACLE_USER/PASSWORD` | 비어 있으면 RTIMS Oracle runtime 계정 사용 |
| SAP HANA | `SAP_HANA_HOST/PORT/USER/PASSWORD` | HRD와 Collector 공통 fallback. 서버별 값은 `PO_SERVERS_JSON[].collectors[]`가 우선 |
| Oracle IFS | `IFS_ORACLE_HOST/PORT/SERVICE/USER/PASSWORD` | IFS 동기화 전용 연결 |
| SAP PO | `SAP_PO_USER/PASSWORD`, `PO_SERVERS_JSON` | 서버별 URL·계정·endpoint가 공통값보다 우선 |

설정값은 backend의 `app/core/config.py`에서만 읽는다. bootstrap API는 SID·표시명·환경·capability처럼 공개 가능한 값만 frontend에 전달하며 URL과 credential을 응답하지 않는다. 로컬 Oracle smoke test의 폐기용 계정은 `RTIMS_TEST_ORACLE_*` 프로세스 환경 변수로만 전달하고 운영 `.env` 또는 Git에 저장하지 않는다.

현재 저장소의 실제 접속정보 유출 검사는 작업 트리와 Git 이력을 함께 대상으로 한다. 과거 분석 자료·압축 해제 폴더·원본 testdata는 저장소 밖의 별도 자료이므로 실행 전 평문 credential과 자동 활성화 값을 반드시 확인한다.

### 현재 검증 범위

- Python 3.11.7 backend 테스트와 Next.js production build를 통과한다.
- 일회용 loopback Oracle에서 Collector buffer 적재, `process_msg_logs`, 복합 checkpoint, 상태 projection과 transaction rollback을 검증했다.
- 실제 사내 RTIMS Oracle SQL 필드·단위, HANA→Oracle 전체 수집, 다중 backend 분산 잠금은 사내 검증 대상이다.
- 세부 기능별 완료·부분·사내검증 상태는 [`docs/LEGACY_FEATURE_COVERAGE.md`](docs/LEGACY_FEATURE_COVERAGE.md)를 기준으로 한다.

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

& "C:\Program Files\PostgreSQL\17\bin\psql.exe" `
  -h localhost -p 5432 -U postgres -d po_monitor `
  -f backend\migrations\006_rtims_compatibility.sql
```

## 서버 추가

`.env`의 `PO_SERVERS_JSON` 배열에 서버를 추가하고 백엔드를 재시작한다. bootstrap API가 공개 가능한 서버 정보만 내려주므로 프론트 선택 목록은 코드 변경 없이 자동 갱신된다.

실제 SAP 서버 주소와 계정은 `.env`에만 작성한다. `.env.example`에는 운영값을 커밋하지 않는다.

서버별로 `base_url`, `port`, `username`, `password`를 독립적으로 설정할 수 있다. `username` 또는 `password`를 생략하거나 빈 값으로 두면 공통 `SAP_PO_USER`, `SAP_PO_PASSWORD`를 사용한다. 서버마다 WSDL 또는 HTTP 경로도 다르면 `endpoint_paths`에서 해당 경로만 덮어쓴다. WSDL이 DNS에서 해석되지 않는 short hostname을 내부 참조로 발행하면 `host_aliases`에 그 이름만 추가한다.

```env
SAP_PO_USER=공통-fallback-user
SAP_PO_PASSWORD=공통-fallback-password
PO_SERVERS_JSON=[{"sid":"POP","display_name":"PO Production","environment":"production","base_url":"https://pop-host.example","port":50000,"username":"pop-user","password":"pop-password","capabilities":["monitor","audit"]},{"sid":"PMP","display_name":"PO Production 2","environment":"production","base_url":"https://pmp-host.example","port":60000,"username":"pmp-user","password":"pmp-password","endpoint_paths":{"channels":"/custom/CommunicationChannel?wsdl","directory":"/custom/dir/read/ext"},"capabilities":["monitor","audit","hrd"]}]
```

RTIMS 수집 서버에는 `collector` capability와 `collectors` 배열을 추가한다. profile마다 HANA host·port·계정·schema, `BE|EO`, 간격, 조회 상한을 독립 설정할 수 있다. `oracle_instance_id`는 전체 서버에서 중복되면 backend가 시작 전에 거부한다. 실제 단일 행 예시는 [`.env.example`](.env.example)을 따른다.

`endpoint_paths`에서 사용할 수 있는 키는 다음과 같다.

| 키 | 대상 |
|---|---|
| `channels` | CommunicationChannelIn WSDL |
| `channel_admin` | ChannelAdmin WSDL |
| `adapter_monitor` | AdapterMessageMonitoring WSDL |
| `aae_monitor` | AaeMessageMonitor WSDL |
| `systatus` | Systatus WSDL |
| `business_system` | BusinessSystemIn WSDL |
| `interface_monitor` | InterfaceMonitor WSDL |
| `directory` | Directory HTTP 경로 |
| `hrd_test` | HRD HttpMessageServlet 경로 |

`base_url`, 계정, 비밀번호, `endpoint_paths`는 backend 내부에서만 사용하며 bootstrap과 프론트 응답에는 노출하지 않는다.

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
