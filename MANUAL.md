# 프로젝트 MANUAL

## 프로젝트 생성 규칙

- 큰 뿌리는 반드시 `frontend`와 `backend`로 분리한다.
- 기능은 기술 계층이 아니라 업무 도메인 단위로 배치한다.
- 각 영역과 각 도메인은 `README.md`, `MANUAL.md`, `SKILL.md`, `ERROR.md`를 가진다.
- 공통 코드는 `core`에 두되, 한 도메인에서만 쓰는 코드는 그 도메인 밖으로 이동하지 않는다.

## 신규 도메인 생성

1. frontend/backend 중 책임 영역을 결정한다.
2. `<area>/src/domains/<domain>` 또는 `backend/app/domains/<domain>`을 만든다.
3. 네 문서를 먼저 만들고 public API와 책임 경계를 적는다.
4. 구현·테스트를 추가한다.
5. 루트 및 영역 README의 도메인 지도에 등록한다.

## 오류 기록 규칙

해결된 오류는 대상 도메인의 `ERROR.md`에 다음 형식으로 남긴다.

```text
## YYYY-MM-DD / 짧은 제목
- 증상:
- 영향:
- 원인:
- 해결:
- 검증:
- 재발 방지:
- 관련 파일 또는 커밋:
```

영역을 넘는 오류는 루트 `ERROR.md`에도 요약한다. 비밀번호, 토큰, 실제 SAP 주소, 개인정보는 기록하지 않는다.

## 환경·서버 규칙

- `.env`가 로컬 설정의 단일 원본이며 실제 값은 Git에 올리지 않는다.
- 프론트 공개값만 `NEXT_PUBLIC_` 접두사를 사용한다.
- 서버 추가는 `PO_SERVERS_JSON`으로 처리한다.
- SID는 2~8자 대문자·숫자, PostgreSQL 식별자는 소문자 snake_case를 사용한다.

## 도메인 요약

- `auth`: 인증과 역할
- `configuration/server`: 서버 등록과 선택
- `dashboard/monitoring`: 사용자 화면 구성과 운영 지표
- `channels/messages/interfaces`: SAP PO 핵심 조회
- `incidents/alerts`: 장애 이력과 실시간 대응
- `collectors`: 부하를 고려한 증분 수집
- `llm_search`: 매뉴얼·오류 이력을 활용할 분석 계약
