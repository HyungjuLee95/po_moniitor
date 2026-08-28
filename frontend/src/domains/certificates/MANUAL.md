# Certificates MANUAL

- 현황 메뉴의 `인증서 만료 현황`에서 선택 SID를 조회한다.
- 임박 기준을 변경하면 backend가 상태와 D-day를 다시 계산한다.
- 만료일 서비스가 없는 서버는 View·Alias·DN을 표시하고 상태를 `만료일 미확인`으로 구분한다.
- 검색은 View, Alias, Subject/Issuer DN, Serial에 적용한다.
- CSV는 현재 화면 필터 결과만 내보내며 Excel formula로 해석될 수 있는 선행 문자는 보호한다.
