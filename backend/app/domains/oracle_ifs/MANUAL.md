# Oracle IFS MANUAL

- RTIMS Oracle과 별도 접속 설정을 사용한다.
- Oracle 원본은 읽기 전용이며 사용자 ID 목록을 bind 변수로 제한한다.
- PostgreSQL cache는 `req_seq` 기준 upsert한다.
- 수동 동기화는 ADMIN, 이관 예정일 변경은 ADMIN·OPERATOR만 허용한다.
- 스케줄러는 환경변수로 활성화하며 한 프로세스에서 중복 실행하지 않는다.
