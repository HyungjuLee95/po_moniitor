# 프로젝트 MANUAL

## 프로젝트 생성 규칙

- 큰 뿌리는 반드시 `frontend`와 `backend`로 분리한다.
- 기능은 기술 계층이 아니라 업무 도메인 단위로 배치한다.
- 각 영역과 각 도메인은 `README.md`, `MANUAL.md`, `SKILL.md`, `ERROR.md`, `API.md`를 가진다.
- 공통 코드는 `core`에 두되, 한 도메인에서만 쓰는 코드는 그 도메인 밖으로 이동하지 않는다.

## 신규 도메인 생성

1. frontend/backend 중 책임 영역을 결정한다.
2. `<area>/src/domains/<domain>` 또는 `backend/app/domains/<domain>`을 만든다.
3. 다섯 문서를 먼저 만들고 public API와 책임 경계를 적는다.
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

검증 중 발생한 프로젝트 공통 오류는 루트 `ERROR.md`, 특정 도메인에서만 발생한 오류는 해당 도메인의 `ERROR.md`에 즉시 기록한다. `API.md`에는 오류 원인이 아니라 정상 계약만 유지한다.

## API 문서 규칙

- 백엔드 도메인의 `API.md`에는 method, path, permission, server capability, request, response, 외부 원본을 기록한다.
- 프론트 도메인의 `API.md`에는 호출 API, 사용 화면, 권한, 로딩·오류·파일 다운로드·SSE 처리 계약을 기록한다.
- API를 추가·변경·삭제할 때 구현 및 테스트와 같은 변경에서 `API.md`를 갱신한다.
- 내부 URL, 계정, 비밀번호, 토큰과 메시지 payload 원문은 기록하지 않는다.

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
- `workspaces`: 사용자 소유 작업과 단계별 진행
- `settings`: 공개 가능한 연결 준비 상태 점검
- `llm_search`: 매뉴얼·오류 이력을 활용할 분석 계약
- `hrd`: HRD 분배 인터페이스·Excel·테스트 메시지
- `oracle_ifs`: 별도 Oracle IFS 동기화와 PostgreSQL cache
- `posts`: 운영 지식 게시글

HRD는 필수 이식 범위다. HRD 도메인의 다섯 문서와 메뉴·API·데이터 원본을 함께 유지한다.

## 운영 메뉴 원칙

- 메뉴는 기술 API가 아니라 `현황 → 추적·분석 → 채널 운영 → HRD 업무 → 업무 도구 → 관리`의 실제 사용 흐름을 따른다.
- 채널 컨트롤과 Excel 대량 변경, HRD 조회와 테스트 전송은 권한과 작업 위험이 다르므로 독립 메뉴로 유지한다.
- 사용자가 고정한 메뉴와 사용 빈도가 높은 메뉴는 `자주 사용하는 메뉴`에 노출하되 서버 권한으로 허용된 메뉴만 표시한다.
- Legacy 연결 상태는 판단 원본이 확인되기 전 정상·오류를 추정하지 않고 `데이터 원본 설정 필요`로 표시한다.

## 사용자 역할

- `ADMIN`은 화면 표시명을 `admin`으로 사용하고 사용자·환경 설정을 포함한 전체 권한을 가진다.
- `OPERATOR`는 화면 표시명을 `관리자`로 사용하고 조회·채널 운영 권한을 가진다.
- `VIEWER`는 화면 표시명을 `일반`으로 사용하고 조회 전용 권한을 가진다.
- 메뉴 숨김은 보조 UX이며 permission과 서버 접근 범위는 백엔드에서 다시 검사한다.
