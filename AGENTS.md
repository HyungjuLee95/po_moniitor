# PO_MONITOR_MAIN AI 작업 규칙

## 1. 목적

이 문서는 AI와 개발자가 프로젝트를 탐색하고 구현·검증·문서화하는 공통 규칙의 기준이다. 프로젝트 목표와 전체 도메인 지도는 `PROJECT.md`, 현재 작업 범위는 `CURRENT_TASK.md`, 도메인 계약은 각 도메인의 `README.md`와 `API.md`를 기준으로 한다.

## 2. 기본 읽기 파이프라인

모든 작업은 다음 순서로 시작한다.

1. `AGENTS.md`
2. `PROJECT.md`
3. `CURRENT_TASK.md`
4. 작업 유형에 필요한 루트 또는 영역 문서
5. 대상 도메인의 `README.md`, `MANUAL.md`, `SKILL.md`, `ERROR.md`, `API.md`
6. 관련 소스 코드와 테스트

저장소 전체를 무작정 읽지 않는다. 먼저 파일 트리, 키워드, 심볼, 테스트 이름을 검색하고 필요한 파일만 연다.

## 3. 문서 단일 기준

| 정보 | 기준 문서 |
|---|---|
| AI 작업·안전 규칙 | `AGENTS.md` |
| 목표, 제약, 전체 도메인 지도 | `PROJECT.md` |
| 현재 작업 범위와 완료 조건 | `CURRENT_TASK.md` |
| 마일스톤과 후속 우선순위 | `ROADMAP.md` |
| 설치·실행·빌드·운영 | 루트 또는 영역 `MANUAL.md` |
| 영역·도메인 책임과 코드 지도 | 해당 `README.md` |
| 작업 순서와 금지사항 | 해당 `SKILL.md` |
| 정상 API·외부 연동 계약 | 도메인 `API.md` |
| 오류와 재발 방지 지식 | 해당 `ERROR.md` |
| 사용자·운영 영향 변경 | `CHANGELOG.md` |

같은 설명을 여러 문서에 복사하지 않고 기준 문서에 링크와 짧은 요약만 둔다.

## 4. 영역과 도메인 경계

- 큰 뿌리는 `frontend`와 `backend`로 분리한다.
- 프론트 도메인은 `frontend/src/domains/<domain>`, 백엔드 도메인은 `backend/app/domains/<domain>`에 둔다.
- 각 영역은 `README.md`, `MANUAL.md`, `SKILL.md`, `ERROR.md`를 가진다.
- 각 도메인은 `README.md`, `MANUAL.md`, `SKILL.md`, `ERROR.md`, `API.md`를 가진다.
- `README.md`는 책임·제외 범위·의존 관계, `API.md`는 route·permission·request/response·외부 원본·frontend consumer의 기준이다.
- 공통 코드는 `core`에 두되 한 도메인에서만 쓰는 코드를 성급하게 공통화하지 않는다.

## 5. 작업 유형별 라우팅

- 새 기능: `PROJECT -> CURRENT_TASK -> requirements -> 도메인 README/API/SKILL -> 코드와 테스트`
- 버그 수정: `PROJECT -> CURRENT_TASK -> 도메인 README/API/ERROR/SKILL -> 실패 코드와 테스트`
- 리팩터링: `PROJECT -> CURRENT_TASK -> 공개 계약 -> 기존 테스트 -> 코드`
- 빌드·환경 오류: `PROJECT -> 루트 MANUAL/ERROR -> 설정과 실패 로그 -> 관련 영역`
- 요구사항·아키텍처 변경: `PROJECT -> requirements/architecture -> 관련 도메인 -> ADR -> ROADMAP`
- 배포: `PROJECT -> MANUAL -> deployment -> quality-gates -> 검증 결과 -> CHANGELOG`

수정 전에 작업 목표, 주 도메인, 영향 도메인, 공개 계약 영향, 완료 조건을 정한다. 사용자 요청과 현재 코드가 충돌하면 추정으로 계약을 만들지 말고 확인 가능한 근거를 먼저 찾는다.

## 6. 구현과 검증

1. 목표와 수용 기준 확인
2. 최소 변경 범위 결정
3. 테스트 추가 또는 기존 검증 기준 확인
4. 구현
5. 정적 검사·컴파일
6. 도메인 단위 테스트
7. 필요한 통합·회귀 테스트
8. 실제 환경 검증이 불가능하면 미검증 항목과 이유 명시

실행하지 않은 테스트를 통과했다고 표현하지 않는다. 프론트·백엔드 작업 폴더와 요구 버전을 명시하고 검증한다.

## 7. 문서 역방향 갱신

코드 변경 후 다음을 확인한다.

- 책임·입출력·의존 관계 변경: 도메인 `README.md`
- API·권한·외부 원본 변경: 도메인 `API.md`
- 실행·설정·디버깅 변경: 관련 `MANUAL.md`
- 새 절차·금지사항: 관련 `SKILL.md`
- 오류 또는 검증 실패: 관련 `ERROR.md`
- 프로젝트 흐름·도메인 관계: `PROJECT.md`
- 일정·우선순위: `ROADMAP.md`
- 중요한 기술 결정: `docs/decisions/` ADR
- 사용자·운영 영향: `CHANGELOG.md`

문서는 추가만 하지 않는다. 낡은 설명은 수정·삭제하고 완료된 임시 작업 정보는 안정 문서에 필요한 부분만 반영한 뒤 `CURRENT_TASK.md`를 `IDLE`로 되돌린다.

## 8. 오류 기록 규칙

모든 해결된 결함과 검증 실패를 기록한다. 특정 도메인 오류는 해당 도메인의 `ERROR.md`, 여러 영역에 영향을 주는 오류와 빌드·환경 오류는 루트 `ERROR.md`에 기록한다.

반드시 포함할 내용:

- 증상과 영향
- 확인된 원인
- 해결 방법
- 실제 검증
- 재발 방지
- 관련 파일 또는 명령

`API.md`에는 오류 이력이 아니라 정상 계약만 기록한다.

## 9. 보안·환경·데이터 규칙

- `.env`, SAP·RTIMS·DB 계정, 내부 URL, 토큰, 메시지 payload 원문을 코드·문서·로그·응답에 노출하지 않는다.
- 브라우저에는 공개 가능한 `NEXT_PUBLIC_` 값만 전달하고 인증·권한은 백엔드에서 다시 검사한다.
- LLM에는 마스킹된 운영 문맥만 전달한다.
- PostgreSQL 식별자는 소문자 `snake_case`를 사용한다.
- 적용된 migration을 수정하지 않고 새 순번 migration을 추가한다.
- 서버 추가는 `.env`의 `PO_SERVERS_JSON`과 backend bootstrap 계약을 사용한다.

## 10. 충돌 우선순위와 완료 보고

충돌 우선순위는 `현재 사용자 요청 -> AGENTS.md -> PROJECT.md -> 도메인 README/API -> 승인된 ADR -> 테스트 -> 나머지 문서`다.

완료 보고에는 다음만 간결하게 포함한다.

1. 달성한 결과
2. 실제 실행한 검증
3. 갱신한 주요 문서
4. 확인하지 못한 항목과 남은 위험
