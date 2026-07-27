# Auth 작업 규칙

비밀번호 평문 저장·로그 출력을 금지한다. 권한 검사는 프론트 표시 여부와 무관하게 백엔드 dependency에서 수행한다. 인증 변경 시 ADMIN, OPERATOR, VIEWER 각각의 허용·거부 테스트를 추가한다.
