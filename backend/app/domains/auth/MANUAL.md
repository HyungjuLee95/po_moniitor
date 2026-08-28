# Auth MANUAL

The local demo default is `admin / 1234`. This short password is for the isolated demo mode only. Production must use `DEMO_MODE=false` and PostgreSQL-backed users with the normal password policy.
데모 모드는 환경 Administrator를 사용하고 운영 모드는 `iam` schema를 조회한다. 비밀번호는 PBKDF2 hash만 저장한다. `ADMIN/Administrator`, `OPERATOR/관리자`, `VIEWER/일반` 역할을 사용하고 사용자별 `iam.user_server` 범위를 SID API에서 검사한다.

공개 가입은 `VIEWER`, `active=false`, `first_login=false`, 서버 범위 없음으로만 생성한다. 가입자가 정한 비밀번호를 사용하므로 최초 변경 플래그는 세우지 않는다. Administrator가 역할·서버를 지정하고 활성화해야 인증된다. 설정된 Administrator username은 활성 ADMIN으로 고정하며 다른 계정의 ADMIN 생성·승격을 거부한다.

JWT가 유효해도 매 요청에서 현재 계정의 활성 상태·역할·서버 범위를 다시 조회한다. 계정 비활성화와 권한 변경은 기존 token에도 즉시 적용된다.

비밀번호 찾기는 사용자 존재 여부를 공개하지 않는다. 요청 후 ADMIN이 30분 유효 1회 토큰을 발급하고 사용자에게 내부 절차로 전달한다. DB에는 토큰 hash만 저장한다.
