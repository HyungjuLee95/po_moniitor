# Auth MANUAL
credential은 form으로 전송하고 token은 sessionStorage에만 보관한다. `ADMIN`은 `Administrator`, `OPERATOR`는 `관리자`, `VIEWER`는 `일반`으로 표시한다. 역할별 메뉴는 보조 UX이며 permission과 서버 접근 권한 원본은 backend다.

가입 신청은 표시 이름, 소문자 사용자 ID, 8자 이상 비밀번호와 확인값을 받는다. 가입 완료 후 자동 로그인하지 않고 Administrator 승인 필요 상태를 명확히 표시한다. Administrator 화면은 가입 대기 사용자를 활성 사용자보다 먼저 보여주며 역할과 하나 이상의 접근 서버를 지정해야 승인할 수 있다. 추가 Administrator 선택지는 제공하지 않는다.

비밀번호 찾기는 관리자 승인 요청을 만들고, ADMIN이 발급한 1회 토큰으로 로그인 화면에서 재설정한다. 토큰은 저장하지 않는다.
