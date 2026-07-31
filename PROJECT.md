# PO_MONITOR_MAIN 프로젝트 지도

## 한 줄 목표

SAP PO와 RTIMS 운영자가 여러 서버의 메시지·채널·인터페이스·장애를 한 화면에서 안전하게 조회하고 제어하도록 지원한다.

## 대상 사용자

- `ADMIN(admin)`: 사용자·권한·환경·대량 작업을 포함한 전체 관리
- `OPERATOR(관리자)`: 운영 조회, 채널 제어, 장애 처리
- `VIEWER(일반)`: 허용된 서버와 메뉴의 조회
- 사용 환경: 인터넷 연결이 제한된 Windows 사내망

## 현재 제품 범위

- `.env` 기반 SAP PO 서버 registry와 동적 서버 선택
- 사용자·역할·서버 접근 권한
- 24시간 트래픽, 시스템 처리 결과, Queue, 리소스 대시보드
- 채널 상태·시스템별 채널 정보·단건 및 대량 제어
- 채널 검색에서 메시지 목록을 거쳐 Message ID Audit을 조회하는 추적 흐름
- HRD 인터페이스 선택 조회·Excel·테스트 메시지·일일 점검
- RTIMS 통계·장애·실시간 인터페이스와 Oracle IFS 동기화
- 사용자별 대시보드·즐겨찾기·워크스페이스·운영 게시글
- JSON 계약 기반 LLM 장애 분석 중계 형태

세부 구현 상태와 사내 실검증 필요 항목은 [`docs/LEGACY_FEATURE_COVERAGE.md`](docs/LEGACY_FEATURE_COVERAGE.md)가 기준이다.

## 제외 및 보류 범위

- 실제 사내 SAP PO·RTIMS 연결값과 운영 계정의 저장
- 확인되지 않은 Legacy 정상·오류 상태 추정
- 실제 RTIMS Alert Inbox와 내부 LLM 연동 완료 판정
- 다중 인스턴스 Collector 분산 잠금 완료 판정

## 공통 제약

| 영역 | 기준 |
|---|---|
| Python | 3.11.7, 사내망에서는 가상환경 미사용 |
| Frontend | 공식 Next.js 16.2.12 App Router, React 19.2.7, npm 11.13.0 |
| Backend | FastAPI, Python 모듈 실행 방식 |
| Database | PostgreSQL 17 권장, 소문자 `snake_case`, 순번 migration |
| External | SAP PO, RTIMS Oracle, 선택적 HANA·Oracle IFS·내부 LLM |
| Security | 비밀값은 루트 `.env`에만 저장하고 frontend로 전달하지 않음 |
| Availability | 외부 연동 지연 시 timeout·부분 fallback·기존 화면 유지 |

## 전체 사용자 흐름

```text
로그인
  -> 권한·서버 범위 bootstrap
  -> 현황 대시보드 또는 업무 메뉴 선택
  -> SAP PO/RTIMS/DB 조회
  -> 상세 추적 또는 권한 기반 운영 작업
  -> 결과·오류·진행 상태 표시
```

## 시스템 데이터 흐름

```text
Browser (Next.js)
  -> FastAPI permission boundary
     -> SAP PO API / SOAP
     -> RTIMS Oracle
     -> PostgreSQL
     -> Oracle IFS / HANA (optional)
     -> Internal LLM JSON API (optional, masked context only)
```

## 영역 지도

| 영역 | 책임 | 기준 문서 |
|---|---|---|
| Frontend | 화면, 상태, 권한별 메뉴, 비동기 로딩과 fallback | [`frontend/README.md`](frontend/README.md) |
| Backend | 인증·권한, 도메인 API, 외부 연동, PostgreSQL | [`backend/README.md`](backend/README.md) |
| SAP PO integration | Directory·Channel·Audit·InterfaceMonitor 호출 | [`backend/app/integrations/sap_po/README.md`](backend/app/integrations/sap_po/README.md) |
| RTIMS integration | Oracle 조회와 RTIMS 데이터 변환 | [`backend/app/integrations/rtims/README.md`](backend/app/integrations/rtims/README.md) |

## 도메인 지도

| 논리 도메인 | 책임 | Frontend | Backend |
|---|---|---|---|
| alerts | 실시간 알림과 확인 | [`README`](frontend/src/domains/alerts/README.md) | [`README`](backend/app/domains/alerts/README.md) |
| auth | 로그인·세션·역할 | [`README`](frontend/src/domains/auth/README.md) | [`README`](backend/app/domains/auth/README.md) |
| channels | 채널 상태·정보·제어·대량 작업 | [`README`](frontend/src/domains/channels/README.md) | [`README`](backend/app/domains/channels/README.md) |
| collectors | checkpoint와 증분 수집 | [`README`](frontend/src/domains/collectors/README.md) | [`README`](backend/app/domains/collectors/README.md) |
| configuration/server/settings | 서버 registry·선택·환경 및 사용자 설정 | [`server`](frontend/src/domains/server/README.md), [`settings`](frontend/src/domains/settings/README.md) | [`configuration`](backend/app/domains/configuration/README.md) |
| dashboard | 사용자별 위젯·즐겨찾기·요약 지표 | [`README`](frontend/src/domains/dashboard/README.md) | [`README`](backend/app/domains/dashboard/README.md) |
| hrd | HRD 조회·Excel·테스트 메시지·일일 점검 | [`README`](frontend/src/domains/hrd/README.md) | [`README`](backend/app/domains/hrd/README.md) |
| incidents | 장애 목록·상세·처리 | [`README`](frontend/src/domains/incidents/README.md) | [`README`](backend/app/domains/incidents/README.md) |
| interfaces | 시스템·Namespace·topology 기준정보 | [`README`](frontend/src/domains/interfaces/README.md) | [`README`](backend/app/domains/interfaces/README.md) |
| llm_search | 마스킹된 장애 분석 JSON 계약 | [`README`](frontend/src/domains/llm_search/README.md) | [`README`](backend/app/domains/llm_search/README.md) |
| messages | 채널 메시지 목록·Message ID·CC 로그 | [`README`](frontend/src/domains/messages/README.md) | [`README`](backend/app/domains/messages/README.md) |
| monitoring | 트래픽·처리 결과·리소스·Queue | [`README`](frontend/src/domains/monitoring/README.md) | [`README`](backend/app/domains/monitoring/README.md) |
| oracle_ifs | Oracle IFS 동기화와 PostgreSQL cache | [`README`](frontend/src/domains/oracle_ifs/README.md) | [`README`](backend/app/domains/oracle_ifs/README.md) |
| posts | 운영 지식 게시글 | [`README`](frontend/src/domains/posts/README.md) | [`README`](backend/app/domains/posts/README.md) |
| workspaces | 사용자 소유 작업과 단계 진행 | [`README`](frontend/src/domains/workspaces/README.md) | [`README`](backend/app/domains/workspaces/README.md) |

## 현재 단계

- 상태: `BETA / INTERNAL_VALIDATION`
- 현재 마일스톤: 문서 파이프라인 정착과 사내 SAP PO·RTIMS smoke test 준비
- 계획: [`ROADMAP.md`](ROADMAP.md)
- 활성 작업: [`CURRENT_TASK.md`](CURRENT_TASK.md)

## 설계·품질 문서

- 요구사항: [`docs/requirements.md`](docs/requirements.md)
- 아키텍처: [`docs/architecture.md`](docs/architecture.md)
- 테스트: [`docs/testing.md`](docs/testing.md)
- 품질 게이트: [`docs/quality-gates.md`](docs/quality-gates.md)
- 배포: [`docs/deployment.md`](docs/deployment.md)
- 문서 정책: [`docs/documentation-policy.md`](docs/documentation-policy.md)
- 설계 결정: [`docs/decisions/`](docs/decisions/)
