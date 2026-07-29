# Backend ERROR

백엔드 공통 오류를 기록한다. DB 연결, 인증, 환경 변수 검증, SAP 공통 timeout 및 공통 응답 변환 문제는 이 문서와 관련 도메인 ERROR에 함께 남긴다.

## 2026-07-28 / 검증용 Python의 pytest 누락

- 증상: `python -m pytest backend/tests` 실행 시 `No module named pytest`
- 영향: 백엔드 컴파일은 완료됐지만 테스트 수집을 시작하지 못함
- 원인: Codex 검증용 시스템 Python에 개발 요구사항이 설치되지 않음
- 해결: 가상환경을 만들지 않고 검증용 Python에 `backend/requirements-dev.txt`를 설치
- 검증: 설치 후 전체 backend test 재실행, 24개 통과
- 재발 방지: 사내망 개발 PC는 일반 설치 뒤 `requirements-dev.txt`도 설치하고 `python -m pytest --version`을 확인

## 2026-07-28 / 실행 중 백엔드에 신규 route 미반영

- 증상: 소스와 OpenAPI 단위 테스트에는 HRD route가 있으나 실행 중인 localhost OpenAPI에는 표시되지 않음
- 영향: 프론트에서 신규 필수 기능 API를 호출할 수 없음
- 원인: 기존 백엔드 프로세스가 변경 전 모듈 상태를 유지함
- 해결: 검증된 dependency가 설치된 Python으로 uvicorn 프로세스를 재시작
- 검증: localhost health 정상, HRD·채널 대량작업·Oracle IFS·게시글 route 노출 확인
- 재발 방지: router·dependency 변경 후 backend 프로세스를 재시작하고 OpenAPI smoke test 수행

## 2026-07-28 / reload 백엔드 응답 정지

- 증상: 8000 포트는 LISTEN 상태였지만 health와 OpenAPI 요청이 timeout 됨
- 영향: 새 throughput·message filter route 반영 여부와 프론트 API 호출을 확인할 수 없음
- 원인: 장시간 실행된 uvicorn reload 프로세스가 여러 연결을 유지한 채 응답하지 않음
- 해결: 해당 백엔드 프로세스를 종료하고 검증된 Python 환경에서 단일 uvicorn 프로세스로 재시작
- 검증: health `ok`, `/api/v1/monitoring/throughput`와 `/api/v1/messages` OpenAPI 노출 확인
- 재발 방지: route 변경 후 health와 OpenAPI가 timeout이면 포트 존재만 신뢰하지 않고 프로세스를 정상 재시작
