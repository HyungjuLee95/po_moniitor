# Auth MANUAL
credential은 form으로 전송하고 token은 sessionStorage에만 보관한다. `ADMIN`은 `admin`, `OPERATOR`는 `관리자`, `VIEWER`는 `일반`으로 표시한다. 역할별 메뉴는 보조 UX이며 permission과 서버 접근 권한 원본은 backend다.

비밀번호 찾기는 관리자 승인 요청을 만들고, ADMIN이 발급한 1회 토큰으로 로그인 화면에서 재설정한다. 토큰은 저장하지 않는다.
