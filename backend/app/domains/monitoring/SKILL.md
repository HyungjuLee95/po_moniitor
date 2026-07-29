# Monitoring SKILL
서버별 부분 실패와 timeout을 격리한다. 지표 변경 시 계산식·timezone·집계 window를 문서와 테스트에 명시한다.

트래픽 변경 검증 항목:

- 시간 모드는 날짜 경계 안의 `00~23` bucket을 사용한다.
- 일 모드는 지정한 `days`만 조회하며 API 최대값은 31일이다.
- `REQ_MSG_SIZE`, `RES_MSG_SIZE`의 null을 0으로 처리한다.
- POP/PMP 합산은 같은 bucket끼리 더하고 한 서버 실패가 다른 서버 결과를 지우지 않게 한다.
- 데이터가 없는 시간·날짜는 프론트가 0 bucket으로 보완한다.
