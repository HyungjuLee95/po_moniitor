# Auth MANUAL
데모 모드는 환경 계정을 사용하고 운영 모드는 `iam` schema를 조회한다. 비밀번호는 PBKDF2 등 검증된 hash만 저장하며 모든 보호 API는 backend dependency로 권한을 검사한다.
