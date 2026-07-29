# 기존 프로젝트 기능 이식 현황

이 문서는 전달받은 최신 분석 자료와 `PO_MONITOR_MAIN`의 구현 상태를 비교하는 기준표다.
기능이 존재하는 것처럼 보이는 placeholder 화면은 `미구현`으로 분류한다.

## 상태 정의

- `완료`: 백엔드 계약과 실제 UI가 모두 연결됨
- `백엔드 완료`: 실제 API는 있으나 전용 UI가 없음
- `부분`: 일부 조회 또는 요약만 구현됨
- `미구현`: 원본 자료에는 있으나 새 프로젝트에는 아직 없음

## 핵심 기능

| 기능 | 상태 | 현재 위치 또는 남은 작업 |
|---|---|---|
| 로그인·JWT·역할 권한 | 완료 | `auth` |
| `.env` 서버 등록 및 프론트 서버 선택 자동 반영 | 완료 | `configuration`, `server` |
| 사용자별 대시보드 배치·숨김·밀도 설정 | 완료 | `dashboard` |
| 사용자별 즐겨찾기·자주 사용하는 메뉴 | 완료 | dashboard preference의 favorite/recent/usage |
| 실제 24시간 메시지 트래픽 | 완료 | RTIMS 시간 bucket API와 대시보드 그래프 |
| 실시간 인터페이스 내역 | 완료 | 15초 자동 갱신·상태·키워드 필터 |
| 서버별 채널 실시간 상태 | 완료 | `channels` 전용 화면과 `GET /channels` |
| SAP 등록 시스템 목록 | 완료 | 시스템 선택→포함 채널 drill-down UI |
| 시스템에 포함된 채널 조회 | 완료 | `GET /channels/inventory?sid=&component_id=` |
| 채널 상세·Directory 비밀번호 복호화 | 완료 | ADMIN API와 보안 Excel 추출에서만 사용 |
| 채널 시작·중지 | 완료 | 다중 선택 제어와 결과 재조회 |
| 채널 상태 확인·운영 모드 액션 | 완료 | `CHECK`, `AUTOMATIC`, `MANUAL`, `EXTERNAL` |
| Message ID Audit 조회 | 완료 | 전용 검색·타임라인 UI |
| 최근 메시지 조회 | 완료 | RTIMS 또는 AAE API 목록 UI |
| 채널별 RTIMS 통계·메시지 | 완료 | 선택 채널 상세 패널 |
| RTIMS 대시보드·인시던트 | 완료 | 집계·목록·권한 기반 해결 UI |
| RTIMS 성능·리소스·Queue | 완료 | 성능 및 리소스 화면. 내부 DB에서 단위·코드 smoke test 필요 |
| 시스템 topology | 완료 | 송신→수신 그룹과 검색 UI |
| HRD 인터페이스·Excel·테스트 메시지 | 완료 | CommunicationChannelIn, 선택적 HANA, HttpAdapter |
| HRD 현행·7일 Delivering 일일 점검 | 완료 | HRD 조회와 메시지 168시간 preset |
| 채널 대량 Excel·미리보기·SSE 제어 | 완료 | ADMIN Excel, 마스킹 preview, 진행 이벤트 |
| Namespace 인벤토리 | 완료 | SAP InterfaceMonitor 실제 operation 호출 |
| 시스템 그룹 통계·대기 상세 | 완료 | RTIMS PM/통계/MON_Q_STATUS |
| Oracle IFS 동기화 | 완료 | 별도 Oracle 설정, PostgreSQL cache, 수동·선택적 scheduler |
| 게시글·비밀번호 찾기·직접 변경 | 완료 | 소유권 게시글, 관리자 승인형 reset token |
| Collector 상태·수동 실행 | 부분 | PostgreSQL checkpoint와 프로세스 내부 잠금 완료. 시간창 분할·중복 제거·페이지 수집과 다중 인스턴스 분산 잠금은 후속 |
| 장애 알림과 LLM 분석 형태 | 부분 | UI/API 계약은 있으나 실시간 RTIMS 알림과 실제 LLM은 미연결 |
| 프로젝트 워크스페이스 CRUD·단계 진행 | 완료 | owner-scoped PostgreSQL CRUD와 단계 진행 UI |
| 사용자·역할·서버 접근 관리 | 완료 | admin/관리자/일반 역할, PBKDF2 비밀번호, 서버별 백엔드 권한 검사 |
| 응답 지연 drill-down·기준 설정 | 완료 | MON_MSG_LOG 원본 목록과 서버별 policy |

`OperationsWorkspace.tsx`라는 현재 컴포넌트 이름은 화면 전체 shell을 뜻한다.
원본 프로젝트의 작업·전송 상태 관리용 `워크스페이스` 기능이 구현되었다는 뜻은 아니다.

## 후속 이식 대상

| 영역 | 미구현 기능 |
|---|---|
| 채널 운영 | 실제 사내 SAP에서 Excel 필드명·SSE 대량 건수 smoke test |
| 인터페이스 | InterfaceMonitor operation/응답 wrapper 사내 버전 smoke test |
| HRD | HANA 스케줄 조인·HttpAdapter sender 매핑 사내 smoke test |
| RTIMS | LONG_RUNNING 전용 이력 |
| 수집기 | 분산 lock, 스케줄러, 필요 시 증분 결과 영속 저장 |
| 관리 | 비밀번호 만료·로그인 잠금 정책 |
| 모니터링 고도화 | 실제 RTIMS Alert Inbox와 LLM 연동 |
| Legacy 연결 | 정상·오류를 판정할 데이터 원본과 상태 코드 확인 |

## 원본 분석 자료의 근거

- `hynix_project_backend_상세분석.md`
  - Workspaces API
  - SAP PO systems, channel inventory/detail/control/batch/bulk, Audit, HRD API
  - RTIMS dashboard, resource, queue, incident, system, channel-monitor API
- `hynix_project_analysis.md`
  - 15개 메뉴 구성
  - Channel Monitor/Control, Audit, Workspace, System Dashboard, Topology UI
- `RTIMSDEV_상세분석.md`
  - AAE/Systatus Collector, Resource/Queue/Alert/Interface Monitor
- `rtims_sqlmap_analysis.md`
  - RTIMS 테이블과 Alert/Audit SQL 계약
- `RTIMS_Collector_부하감축_메커니즘.md`
  - 증분 수집과 부하 감축 원칙

## 다음 묶음 제안

1. 실제 사내 SAP PO/RTIMS에서 SQL·SOAP 필드와 단위 smoke test
2. 실제 RTIMS Alert Inbox와 LLM 분석 연결
3. Collector 분산 lock·스케줄러
4. 보안 검토를 거친 대량 작업·관리 기능
5. 별도 요구사항을 받은 뒤 HRD 도메인 생성
