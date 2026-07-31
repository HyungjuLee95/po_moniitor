# 시스템 아키텍처

## 설계 목표

- frontend와 backend의 명확한 책임 분리
- 업무 도메인 단위 변경과 문서·코드·테스트의 동일 경계
- 외부 시스템 지연·실패가 전체 화면을 막지 않는 부분 실패 처리
- `.env` 서버 registry를 통한 서버 추가와 UI 자동 반영
- 모든 운영 작업의 백엔드 권한 재검사와 비밀값 차단

## 시스템 컨텍스트

```text
운영 사용자
  -> Next.js Frontend
     -> FastAPI Backend
        -> SAP PO Directory / Channel / Audit / InterfaceMonitor
        -> RTIMS Oracle
        -> PostgreSQL
        -> Oracle IFS / HANA (선택)
        -> 내부 LLM JSON API (선택)
```

브라우저는 외부 시스템과 직접 통신하지 않는다. FastAPI가 인증·권한·서버 접근 범위를 검사하고 응답을 화면 계약으로 변환한다.

## 애플리케이션 계층

| 계층 | 위치 | 책임 |
|---|---|---|
| Presentation | `frontend/app`, `frontend/src/app` | App Router 진입점과 화면 조립 |
| Frontend domain | `frontend/src/domains` | 도메인별 UI·상태·API 소비 계약 |
| Frontend core | `frontend/src/core` | 세션·공통 API client·공통 타입·refresh |
| Backend entry | `backend/app/main.py` | FastAPI 조립, middleware, route 등록 |
| Backend domain | `backend/app/domains` | 업무 규칙·route·service·repository 계약 |
| Integration | `backend/app/integrations` | SAP PO·RTIMS 외부 호출과 응답 변환 |
| Persistence | PostgreSQL·Oracle repositories | 사용자·설정·cache·운영 원본 조회 |

## 주요 데이터 흐름

### 서버 bootstrap

```text
.env PO_SERVERS_JSON
  -> backend configuration
  -> 공개 가능한 서버 metadata
  -> frontend 서버 선택 목록
```

### 모니터링 조회

```text
Dashboard widget
  -> 독립 API 요청
  -> timeout / cached value 유지 / fallback
  -> 완료된 widget부터 갱신
  -> 15분 background refresh
```

### 메시지 추적

```text
서버·채널 검색
  -> 메시지 목록
  -> Message ID 선택
  -> CC/Audit 로그 타임라인
```

### 채널 대량 작업

```text
Excel 다운로드·수정
  -> 업로드 validation과 masking preview
  -> 권한 확인
  -> SSE 진행 이벤트
  -> 결과·실패 목록
```

## 외부 연동

| 시스템 | 목적 | 인증 위치 | 실패 처리 |
|---|---|---|---|
| SAP PO | 채널·Audit·Directory·InterfaceMonitor | backend `.env` | timeout, capability 오류, 부분 결과 |
| RTIMS Oracle | 메시지·통계·리소스·Queue·장애 | backend `.env` | 비활성화 상태와 명시적 오류 |
| PostgreSQL | 사용자·권한·개인 설정·cache·checkpoint | backend `.env` | transaction rollback과 health 점검 |
| Oracle IFS | 선택적 데이터 동기화 | backend `.env` | 수동 재시도와 마지막 성공 상태 |
| HANA | 선택적 HRD 보강 조회 | backend `.env` | 기본 SAP 결과 유지 |
| Internal LLM | 마스킹된 장애 분석 | backend 루트 `.env`의 `LLM_API_URL` | JSON 계약 검증과 사용자 오류 표시 |

## 신뢰 경계와 보안

- frontend 권한 숨김은 UX일 뿐이며 backend permission이 최종 경계다.
- SAP·RTIMS·DB·LLM 주소와 인증정보는 bootstrap 또는 오류 응답에 포함하지 않는다.
- 원본 메시지 payload와 개인정보는 로그·문서·LLM 요청에서 마스킹한다.
- 대량 변경·채널 제어·사용자 관리는 최소 권한과 감사 가능 결과를 요구한다.

## 성능과 가용성

- 대시보드 API는 독립적으로 로드하며 한 API 지연이 다른 widget을 막지 않는다.
- 페이지를 유지한 채 기존 데이터를 보여주고 background refresh 결과만 교체한다.
- Collector는 시간창·페이지·checkpoint 단위로 외부 시스템 부하를 제한한다.
- 실제 임계값과 시간 단위는 사내 데이터 원본으로 검증하기 전 확정하지 않는다.

## 주요 설계 결정

- [`ADR-001`](decisions/ADR-001-ai-md-pipeline.md): 기존 도메인 문서 계약을 보존한 AI MD 파이프라인 적용
- 새 결정은 [`ADR-000-template.md`](decisions/ADR-000-template.md)를 복사해 기록한다.
