# 프로젝트 ERROR

## 2026-07-29 / Commit 전 민감정보 검사 명령의 PowerShell 따옴표 오류

- 증상: `rg` 정규식 검사 명령이 `The string is missing the terminator`로 종료됨
- 영향: 파일 변경은 없었고 첫 번째 민감정보 검사가 실행되지 않음
- 원인: PowerShell 명령 문자열 안에서 작은따옴표를 함께 사용하며 문자열 경계가 깨짐
- 해결: 단순한 큰따옴표 패턴으로 다시 실행하고 `.env.example`, 코드, 문서의 credential 관련 항목을 확인함
- 검증: 재실행한 검사가 정상 종료되었고 실제 `.env`는 Git ignore 상태임을 확인함
- 재발 방지: PowerShell에서 복합 정규식은 따옴표 종류를 하나로 단순화하고 먼저 작은 범위에서 실행함
- 관련 파일 또는 커밋: 없음

## 2026-07-28 / External integration waits blocked dashboard loading

- Symptom: independent dashboard widgets all remained in loading state.
- Impact: the development preview was unusable without internal-system connectivity.
- Cause: independent loading and 15-minute refresh were implemented without a browser request deadline.
- Resolution: added a common API timeout and a 12-second dashboard limit with per-widget fallback behavior.
- Verification: frontend validation and local browser confirmation after the timeout window.
- Prevention: define independent loading, timeout, fallback, and background cache retention together for every external API.
- Related: `frontend/src/core/api.ts`, `frontend/src/core/refresh.ts`

공통 또는 여러 도메인에 영향을 주는 오류 이력을 기록한다. 도메인 내부 오류는 해당 도메인의 `ERROR.md`가 원본이다.

## 2026-07-28 / Windows Git 저장소 소유권 불일치

- 증상: `detected dubious ownership`
- 원인: Codex 샌드박스 계정과 사용자 계정의 Windows SID가 다름
- 해결: 해당 저장소 경로만 `safe.directory`로 등록
- 재발 방지: 새 저장소 생성 후 사용자 계정에서 Git 상태를 확인

## 2026-07-28 / 사내망 설치 문서의 가상환경 의존

- 증상: 사내망에서 허용되지 않는 `venv` 생성 및 활성화 명령 때문에 백엔드 설치와 실행 절차를 그대로 사용할 수 없음
- 영향: README, 설치 가이드와 백엔드 시작 배치가 사내 운영 환경과 불일치
- 원인: 초기 개발 환경의 가상환경 사용 방식을 사내망 설치 절차에도 적용함
- 해결: Python 3.11.7 시스템 환경에 직접 설치하고 `python -m pip`, `python -m uvicorn`, `python -m pytest`로 실행하도록 통일
- 검증: 모든 Markdown 및 시작 배치에서 가상환경 생성·활성화 명령 의존 제거 여부 확인
- 재발 방지: 사내망 설치·실행 전에 `python --version`으로 3.11.7을 확인하고 모듈 실행은 항상 `python -m` 형식을 사용

## 2026-07-28 / 잘못된 작업 폴더에서 백엔드 검증 실행

- 증상: `frontend` 폴더에서 `backend/tests`를 실행해 경로를 찾지 못함
- 영향: 같은 명령 묶음의 백엔드 테스트가 실행되지 않음
- 원인: frontend 검증과 backend 검증의 작업 폴더를 분리하지 않음
- 해결: backend 검증은 프로젝트 루트, frontend 검증은 `frontend` 폴더에서 각각 실행
- 검증: 프로젝트 루트에서 backend 24개 test 통과, frontend 폴더에서 lint·build·render test 통과
- 재발 방지: 영역별 검증 명령의 working directory를 명시

## 2026-07-28 / 검증 파일명 추정과 기본 Python 불일치

- 증상: 존재하지 않는 테스트·repository 파일명을 직접 지정했고 기본 `python`은 3.13을 가리켜 pytest를 실행하지 못함
- 영향: 첫 백엔드 검증 명령이 실행되지 않음
- 원인: 실제 파일 목록과 `py -0p` 결과를 확인하기 전에 경로와 interpreter를 추정함
- 해결: `rg --files backend/tests`로 실제 테스트를 확인하고 Codex 검증용 Python의 pytest로 전체 테스트를 실행함
- 검증: Python 3.12 검증 환경에서 backend 25개 테스트 통과
- 재발 방지: 검증 전에 실제 파일 목록과 `python --version`을 확인한다. 사내 이식 최종 검증은 요구 버전 Python 3.11.7에서 별도로 수행한다.

## 2026-07-28 / 실행 중 백엔드 health timeout

- 증상: 8000 포트가 열려 있었지만 health·OpenAPI 요청이 응답하지 않음
- 영향: 프론트의 신규 모니터링 기능이 실행 중 API와 연결되지 않음
- 원인: 장시간 유지된 reload 프로세스 응답 정지
- 해결: 백엔드를 단일 프로세스로 재시작
- 검증: backend health `ok`, 신규 route 2개 노출, frontend HTTP 200 확인
- 재발 방지: 구현 검증은 포트뿐 아니라 health·OpenAPI·frontend HTTP를 함께 확인

## 2026-07-28 / 존재하지 않는 backend test fixture 경로 추정

- 증상: LLM 테스트 구조 확인 중 존재하지 않는 `backend/tests/conftest.py`를 읽으려 해 파일 조회가 실패함
- 영향: 코드 변경 전 테스트 구성 확인 명령 한 건이 실패했으나 구현 파일에는 영향 없음
- 원인: 실제 테스트 파일 목록을 먼저 확인하지 않고 일반적인 pytest fixture 경로를 가정함
- 해결: `rg --files backend/tests`로 실제 테스트 목록을 확인하고 독립 테스트 파일을 추가함
- 검증: 전체 backend pytest로 신규 LLM provider 테스트를 포함해 확인함
- 재발 방지: 테스트 보조 파일을 열기 전에 대상 디렉터리의 실제 파일 목록부터 확인함
