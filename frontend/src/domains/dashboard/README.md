# Dashboard

## Loading and refresh

- Dashboard APIs render independently.
- Each request has a 12-second UI timeout so unavailable SAP PO or RTIMS connections cannot leave every widget loading forever.
- Initial failures show a safe preview or empty state. Background refresh failures keep the last successful data.
- The mounted dashboard refreshes data every 15 minutes without navigation or page reload.
운영 위젯 조립, 업무 흐름형 전역 메뉴, registry, 사용자 배치·표시·밀도와 즐겨찾기·사용 빈도 설정을 담당한다. 기본 대시보드는 메시지 KPI, 실제 24시간 트래픽, 시스템별 처리 결과, Queue·Thread, 실시간 인터페이스와 일일 점검을 제공한다.

트래픽 위젯의 기본 범위는 접근 가능한 POP+PMP 합산이며 위젯 내부에서 서버와 1시간/1일 집계 단위를 선택한다.

전역 메뉴는 `CC 로그 조회`, `MessageID 조회`, `리소스 조회`, `시스템 별 채널 정보` 명칭을 사용하며 리소스 조회는 `현황` 카테고리에 둔다.

대시보드 API는 위젯별로 독립 호출하며 최초에는 영역별 로딩 상태를 표시한다. 이후 화면을 유지한 채 15분마다 기존 값을 보존하면서 백그라운드 갱신한다.
