# 변경 이력

형식은 Keep a Changelog를 참고하되 사용자·운영·개발 절차에 영향을 주는 변경만 기록한다.

## Unreleased

### Added

- 서버별 HANA BE/EO Collector profile과 `(TIMESTAMP, MESSAGE_ID)` 복합 checkpoint
- Oracle Pending 메시지 ID의 bounded HANA 상태 재조회와 신규 checkpoint 분리
- Oracle `MON_BUF_AAE_MSG` batch 적재·`process_msg_logs`·checkpoint·실행 로그 단일 transaction
- Oracle profile별 수집 상태 조회와 수동 실행 필터, 별도 Collector Oracle 계정 fallback
- loopback Oracle에서 buffer·procedure·checkpoint·상태 projection·rollback을 실제 검증하는 smoke script
- `.env` opt-in RTIMS Collector 자동 실행과 시작 지연·고정 지연·SID별 조회 상한
- Collector capability 기반 순차 scheduler, SID 실패 격리와 FastAPI 종료 연동
- 로그인 화면의 공개 가입 신청과 Administrator 승인 대기 흐름
- 가입 대기 사용자 우선 관리, 역할·서버 지정 후 활성화하는 사용자 관리 화면
- SAP PO KeystoreHelp·KeystoreService 기반 인증서 만료 조회 API와 ADMIN·OPERATOR 웹 화면
- 인증서 View·상태·검색 필터, 만료 임박 기준, 상세와 안전한 CSV 내보내기
- Python 3.11.7·requirements·pyproject 동기화를 자동 확인하는 backend contract test
- PostgreSQL·Oracle RTIMS 핵심 14개 객체 DDL과 `.env` 기반 원클릭 생성·컬럼 검증 도구
- 운영 RTIMS runtime 계정과 분리된 Oracle schema-owner 환경 변수
- 프로젝트 목표와 전체 도메인 지도를 관리하는 `PROJECT.md`
- 현재 작업의 읽기·변경·검증 범위를 제한하는 `CURRENT_TASK.md`
- 사내 검증과 운영 고도화를 관리하는 `ROADMAP.md`
- 아키텍처·요구사항·테스트·배포·문서 정책과 ADR 구조
- frontend/backend 도메인 문서와 로컬 링크를 검사하는 자동 품질 게이트

### Changed

- README에 DB·SAP·HANA·IFS 접속정보의 `.env` 단일 원본, 계정 fallback, Git 제외 및 현재 Collector 검증 범위를 명확히 기록
- RTIMS Collector 저장 원본을 Oracle로 확정하고 PostgreSQL은 웹 애플리케이션 데이터와 profile 없는 호환 checkpoint로 제한
- 전역 메뉴를 `현황`, `운영`, `분석`, `관리` 네 카테고리로 재편하고 대시보드 빠른 이동과 compact 화면 밀도를 적용
- ADMIN 표시명을 `Administrator`로 통일하고 추가 ADMIN 생성·승격을 backend에서 차단
- 활성 상태와 서버 범위 변경이 기존 JWT 요청에도 즉시 반영되도록 사용자 권한 확인을 강화
- Python 3.11.7 설치 경로별 의존성이 같도록 requirements와 project metadata를 동기화
- 기존 AI 규칙을 최소 문맥 읽기와 작업 유형별 문서 라우팅 방식으로 확장
- 기존 `README/MANUAL/SKILL/ERROR/API` 도메인 세트를 템플릿의 역할에 맞춰 유지
- SAP PO 서버별 host·port·계정과 WSDL/HTTP 경로 override를 `PO_SERVERS_JSON`에서 관리하고, 미지정 값만 공통 설정으로 fallback하도록 확장
- SAP PO WSDL 내부 short hostname을 서버별 `host_aliases`로 안전하게 치환하도록 연결 호환성 확장
- RTIMS live 조회를 Collector buffer가 아닌 `MON_MSG_LOG`, `MON_INTF_MAP`, `MON_RES_USAGE`, `MON_ERR_HIST` 중심의 SQL-009~018 계약으로 교정하고 메시지 count·리소스 시계열·채널 시간창을 추가

### Fixed

- BusinessSystemIn을 실제 `Query` 계약으로 호출하고 `BusinessSystemID[].ComponentID`를 파싱하도록 교정
- InterfaceMonitor `getAllInterfaces()`와 실제 from/to action 응답을 Namespace 인벤토리로 변환
- 전체 채널 Query에서 ComponentID element를 생략하고 Adapter Audit의 고정 SOAP 파라미터를 모두 전달

### Removed

- 없음
