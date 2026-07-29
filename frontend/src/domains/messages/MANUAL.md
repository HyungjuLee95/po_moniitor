# Messages MANUAL
기본 흐름은 `채널 검색 → 채널 메시지 목록 → 메시지 선택 → Audit timeline`이다. SID와 Message ID를 함께 사용하고 payload 기본 노출을 금지한다.

실시간 인터페이스 화면은 기본 최근 24시간·100건을 조회하고 15초 자동 갱신을 제공한다. 상태는 전체·성공·실패·Delivering으로 필터링하며 상세 접기·펼치기에 payload 원문을 표시하지 않는다.
