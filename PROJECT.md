# PO Monitor Main 프로젝트 기준서

## 목적

여러 SAP PO 서버의 메시지, 채널, 장애 및 수집 상태를 하나의 화면에서 조회하고 권한에 따라 운영 작업을 수행한다.

## 구성

```text
PO_MONITOR_MAIN/
├─ app/                    React 진입점과 전역 스타일
├─ src/
│  ├─ api/                HTTP 클라이언트
│  ├─ auth/               브라우저 세션
│  ├─ components/         로그인·대시보드
│  └─ config/             API 주소·메뉴
├─ backend/
│  ├─ app/core/           환경 설정·보안
│  ├─ app/domains/        업무 도메인
│  ├─ migrations/         PostgreSQL 스키마
│  └─ tests/
└─ docs/                  운영 규칙과 도메인 지식
```

## 요청 흐름

1. 로그인 성공 시 JWT와 사용자 역할을 받는다.
2. 프론트는 bootstrap API에서 역할·권한·서버 목록을 한 번에 받는다.
3. 서버 선택 시 요청에 `sid`만 전달한다.
4. 백엔드는 등록된 SID와 capability를 검증한 뒤 SAP PO API를 호출한다.
5. 비밀번호와 실제 서버 URL은 브라우저 응답에 포함하지 않는다.

## 역할

| 역할 | 범위 |
|---|---|
| ADMIN | 전체 설정, 조회, 운영 작업 |
| OPERATOR | 조회, 채널 제어, 수집 실행, 장애 처리 |
| VIEWER | 읽기 전용 |

## 설계 원칙

- 기능은 `backend/app/domains/<domain>` 단위로 격리한다.
- PostgreSQL 식별자는 소문자 snake_case를 사용하고 따옴표 식별자를 만들지 않는다.
- 서버 증설은 코드 수정이 아닌 `PO_SERVERS_JSON` 변경으로 처리한다.
- 환경 변수의 비밀값은 로그, API 응답, 프론트 번들에 포함하지 않는다.
- SAP PO 호출 어댑터와 화면용 DTO를 분리한다.
