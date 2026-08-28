# Backend

Python 3.11.7/FastAPI/PostgreSQL 기반 API다. `app/core`는 환경·보안, `app/domains`는 업무 기능, `migrations`는 순차 DB 변경을 담당한다.

도메인은 `auth`, `configuration`, `dashboard`, `monitoring`, `channels`, `certificates`, `messages`, `interfaces`, `incidents`, `collectors`, `workspaces`, `alerts`, `llm_search`, `hrd`, `oracle_ifs`, `posts`로 구성한다. API prefix는 `/api/v1`이다.

실제 SAP PO 호출 구현 전 각 도메인의 `MANUAL.md`와 `API.md`에서 endpoint, permission, timeout, 마스킹, 오류 변환 규칙을 확인한다.

## 실행 명령

```powershell
cd D:\toyproject\PO_MONITOR_MAIN
python -m pip install -r backend\requirements.txt
python -m uvicorn app.main:app --app-dir backend --reload --host 0.0.0.0 --port 8000
```

API 문서: `http://localhost:8000/docs`

사내망에서는 Python 가상환경을 생성하지 않는다. `python --version`이 `3.11.7`인지 먼저 확인하고 모든 백엔드 패키지를 해당 시스템 Python에 직접 설치한다. 패키지 설치와 모듈 실행은 `pip` 또는 `uvicorn` 단독 명령 대신 `python -m ...` 형식을 사용한다.

## SAP 연결 smoke test

백엔드 실행 후 로그인 토큰을 발급받아 다음 API를 확인한다.

초기 Administrator 외 사용자는 공개 `POST /auth/register`로 비활성 VIEWER 계정을 신청하고, Administrator가 사용자 관리 API에서 역할·접근 서버·활성 상태를 승인한다.

```text
GET /api/v1/channels?sid=POQ
GET /api/v1/channels/inventory?sid=POQ&component_id=*
GET /api/v1/certificates?sid=POQ&warning_days=30
GET /api/v1/messages?sid=POQ&limit=20
GET /api/v1/interfaces?sid=POQ
GET /api/v1/monitoring/summary?sid=POQ
GET /api/v1/monitoring/performance?sid=POQ&hours=24
GET /api/v1/monitoring/resources?sid=POQ
GET /api/v1/monitoring/queues?sid=POQ
GET /api/v1/monitoring/slow-messages?sid=POQ
GET /api/v1/workspaces
GET /api/v1/hrd/interfaces?sid=POQ
GET /api/v1/interfaces/namespaces?sid=POQ
GET /api/v1/monitoring/system-statistics?sid=POQ
GET /api/v1/oracle-ifs/interfaces
GET /api/v1/posts
```

채널 제어는 `SAP_CONTROL_ALLOWED_SIDS_RAW`에 명시된 SID만 허용한다.

## 데이터 원본 우선순위

| 데이터 | 원본 |
|---|---|
| 채널 실시간 상태 | SAP PO Systatus SOAP |
| 채널 목록·상세 | CommunicationChannelIn SOAP |
| 채널 시작·중지 | ChannelAdmin SOAP |
| 채널 비밀번호 | Directory HTTP API, ADMIN 전용 |
| 인증서 View·Alias·만료일 | KeystoreHelp + KeystoreService SOAP |
| 최근 메시지·대시보드·장애 | 기존 RTIMS Oracle |
| 메시지 audit | AdapterMessageMonitoring SOAP |
| 사용자·권한·개인 대시보드 | PostgreSQL |
| RTIMS Collector buffer·가공·checkpoint | 기존 RTIMS Oracle |

RTIMS가 비활성화되면 최근 메시지와 대시보드는 AaeMessageMonitor SOAP을 사용한다.

## RTIMS schema 준비

`backend/migrations/006_rtims_compatibility.sql`은 PostgreSQL `rtims` 호환 schema, `backend/oracle/001_rtims_monitoring_schema.sql`은 Oracle live 계약용 DDL이다. 원클릭 실행기는 `.env`를 읽으며 접속정보를 인자나 로그로 출력하지 않는다.

```powershell
cd D:\toyproject\PO_MONITOR_MAIN
.\scripts\setup-rtims-databases.ps1 -Target all
.\scripts\setup-rtims-databases.ps1 -Target all -CheckOnly
```

Oracle DDL 계정은 runtime 조회·장애처리 계정과 분리한다. 이 DDL은 현재 backend가 요구하는 14개 객체에 한정되며 전체 RTIMS 제품 schema 복제본이 아니다.

## Collector 자동 실행

`RTIMS_COLLECTOR_ENABLED=true`이면 FastAPI와 함께 Collector scheduler가 시작된다. 대상은 `PO_SERVERS_JSON`의 활성 `collector` capability 서버다. `collectors` profile이 있으면 profile별 HANA host·계정·schema, BE/EO, 고정 지연과 1회 상한으로 순차 실행하며 Oracle buffer·procedure·checkpoint를 한 transaction으로 처리한다.

profile 없는 서버는 기존 SAP PO 메시지 조회와 PostgreSQL checkpoint 호환 경로를 사용한다. 현재 원클릭 Oracle DDL은 조회 API 14개 객체만 생성하므로 Collector profile에는 기존 전체 RTIMS schema와 `MON_BUF_AAE_MSG`, sequence, `process_msg_logs`, runtime params/log 권한이 필요하다. 자동 scheduler는 분산 잠금 전까지 backend 한 인스턴스에서만 실행한다.
