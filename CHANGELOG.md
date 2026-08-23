# 변경 이력

형식은 Keep a Changelog를 참고하되 사용자·운영·개발 절차에 영향을 주는 변경만 기록한다.

## Unreleased

### Added

- Python 3.11.7·requirements·pyproject 동기화를 자동 확인하는 backend contract test
- PostgreSQL·Oracle RTIMS 핵심 14개 객체 DDL과 `.env` 기반 원클릭 생성·컬럼 검증 도구
- 운영 RTIMS runtime 계정과 분리된 Oracle schema-owner 환경 변수
- 프로젝트 목표와 전체 도메인 지도를 관리하는 `PROJECT.md`
- 현재 작업의 읽기·변경·검증 범위를 제한하는 `CURRENT_TASK.md`
- 사내 검증과 운영 고도화를 관리하는 `ROADMAP.md`
- 아키텍처·요구사항·테스트·배포·문서 정책과 ADR 구조
- frontend/backend 도메인 문서와 로컬 링크를 검사하는 자동 품질 게이트

### Changed

- Python 3.11.7 설치 경로별 의존성이 같도록 requirements와 project metadata를 동기화
- 기존 AI 규칙을 최소 문맥 읽기와 작업 유형별 문서 라우팅 방식으로 확장
- 기존 `README/MANUAL/SKILL/ERROR/API` 도메인 세트를 템플릿의 역할에 맞춰 유지
- SAP PO 서버별 host·port·계정과 WSDL/HTTP 경로 override를 `PO_SERVERS_JSON`에서 관리하고, 미지정 값만 공통 설정으로 fallback하도록 확장
- RTIMS live 조회를 Collector buffer가 아닌 `MON_MSG_LOG`, `MON_INTF_MAP`, `MON_RES_USAGE`, `MON_ERR_HIST` 중심의 SQL-009~018 계약으로 교정하고 메시지 count·리소스 시계열·채널 시간창을 추가

### Fixed

- 없음

### Removed

- 없음
