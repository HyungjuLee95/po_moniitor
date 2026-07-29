# HRD MANUAL

- 채널 원본은 `CommunicationChannelIn.Query/Read`이며 패턴은 환경변수로 관리한다.
- SQL 문자열에서는 `FROM` 테이블과 `COMPANY_CD/COMPANY_CO IN (...)`만 파싱하고 원문 전체를 API에 반환하지 않는다.
- 배치 스케줄은 선택적 SAP HANA 연결을 사용하며 미설정 시 `null`로 반환한다.
- 테스트 메시지는 `hrd:test` 권한과 서버 `hrd` capability가 모두 필요하다.
- 테스트 XML과 내부 URL은 로그에 남기지 않는다.
