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
| 서버별 채널 실시간 상태 | 부분 | 대시보드 요약과 `GET /channels`는 연결됨. 전용 채널 화면 필요 |
| SAP 등록 시스템 목록 | 백엔드 완료 | `GET /interfaces`; 시스템→채널 drill-down UI 필요 |
| 시스템에 포함된 채널 조회 | 백엔드 완료 | `GET /channels/inventory?sid=&component_id=`; 시스템 트리 UI 필요 |
| 채널 상세·Directory 비밀번호 복호화 | 백엔드 완료 | `GET /channels/detail`, `GET /channels/detail-with-secret`; 권한별 UI 필요 |
| 채널 시작·중지 | 백엔드 완료 | `POST /channels/control`; 선택·확인·결과 UI 필요 |
| 채널 상태 확인 액션 | 부분 | 시작·중지 뒤 검증은 수행. 독립 `STATUS/CHECK` 액션은 미구현 |
| Message ID Audit 조회 | 백엔드 완료 | `GET /messages/{message_id}/audit?sid=`; 검색·타임라인 UI 필요 |
| 최근 메시지 조회 | 백엔드 완료 | RTIMS 또는 AAE API 연결. 필터·페이징·상세 UI 필요 |
| RTIMS 대시보드·채널 요약·인시던트 | 부분 | 기본 집계·목록·해결 API는 연결됨 |
| Collector 상태·수동 실행 | 부분 | 조회·실행 계약만 있음. DB 저장·checkpoint·스케줄러 필요 |
| 장애 알림과 LLM 분석 형태 | 부분 | UI/API 계약은 있으나 실시간 RTIMS 알림과 실제 LLM은 미연결 |
| 프로젝트 워크스페이스 CRUD·단계 진행 | 미구현 | 별도 `workspace` frontend/backend 도메인 필요 |

`OperationsWorkspace.tsx`라는 현재 컴포넌트 이름은 화면 전체 shell을 뜻한다.
원본 프로젝트의 작업·전송 상태 관리용 `워크스페이스` 기능이 구현되었다는 뜻은 아니다.

## 후속 이식 대상

| 영역 | 미구현 기능 |
|---|---|
| 채널 운영 | SSE 일괄 제어, AUTOMATIC/MANUAL/EXTERNAL 모드, Excel 대량 추출·변경 미리보기 |
| 채널별 모니터링 | 채널별 당일 통계, 메시지 로그 페이징, 선택 메시지 Audit 연결 |
| 인터페이스 | Namespace 인벤토리, 시스템 그룹·모듈 현황, 시스템 topology |
| HRD | HRD 인터페이스 조회, HANA 스케줄 매핑, Excel 다운로드, 테스트 메시지 |
| RTIMS | CPU·Memory·Thread·GC, Queue·Backlog, 시스템 통계와 시스템별 대기 현황 |
| 수집기 | 영속 checkpoint, registry, 중복 방지 lock, 증분 수집 결과 저장 |
| 관리 | 워크스페이스, 사용자 관리, 비밀번호 생명주기, 게시글 |
| 데이터 파이프라인 | Oracle IFS 동기화 화면과 실행 |
| 모니터링 고도화 | 성능·트랜잭션 분석, LONG_RUNNING 이력, 실제 Alert Inbox |

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

## 이식 우선순위 제안

1. 채널 모니터·제어 화면
2. Message ID Audit 검색 화면
3. 서버→등록 시스템→채널 drill-down 화면
4. 채널별 RTIMS 통계·메시지 화면
5. 프로젝트 워크스페이스
6. HRD·Topology·Resource·Queue·대량 작업
