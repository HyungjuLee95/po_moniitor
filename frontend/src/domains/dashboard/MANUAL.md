# Dashboard MANUAL

## Request lifecycle

- Use `DASHBOARD_REQUEST_TIMEOUT_MS` for initial and background dashboard requests.
- When the request limit is reached, end only that widget's loading state.
- Initial failures use a safe preview or empty state; refresh failures preserve existing successful data.

## Visual system

- The console uses a high-contrast forest navigation with sage and pistachio accents derived from the approved green palette.
- Navigation category captions are at least `12px`, and primary menu labels are at least `14px`.
- Pale mint and lime tones are reserved for backgrounds and highlights; body text must remain dark enough for operational readability.
- Status red and amber remain semantic alert colors and must not be replaced by decorative greens.

- 전체 메뉴는 화면에 고정하지 않고 좌측 상단 메뉴 버튼으로 여는 drawer를 사용한다.
- 메뉴는 `현황`, `추적·분석`, `채널 운영`, `HRD 업무`, `업무 도구`, `관리` 카테고리로 나누며 역할에 허용된 항목이 없는 카테고리는 표시하지 않는다.
- 메뉴의 별표는 사용자별 고정 메뉴다. 별표 메뉴와 사용 횟수가 높은 메뉴를 합쳐 최대 5개까지 `자주 사용하는 메뉴`에 표시한다.
- 메뉴 선택, 닫기 버튼, 배경 클릭, `Escape` 입력으로 drawer를 닫을 수 있어야 한다.
- 평균 응답시간의 원본 API 필드는 millisecond를 유지하되 화면은 초 단위 소수점 셋째 자리(`0.000초`)로 표시한다.
- `확인 필요`와 `평균 응답` 카드는 클릭 가능한 요약이며 동일 화면에서 근거 목록을 접기·펼치기로 제공한다.
새 위젯은 `WidgetId`, registry, 기본 layout, backend validator에 등록한다. 사용자 설정은 API가 원본이고 localStorage는 보조 복구값이다.

- 기본 KPI는 총 메시지량, 성공률, 실패 건수, 평균 응답시간이다. 전체 채널 수는 기본 대시보드 KPI로 사용하지 않는다.
- `channel_status`, `server_profile`은 호환성을 위해 registry에는 유지하지만 기본 배치에서는 숨긴다.
- Legacy 연결은 판정 원본이 확정될 때까지 중립 안내만 표시한다.
- 메시지 트래픽 위젯의 서버 필터는 상단의 전역 SID 선택과 독립적이다. 기본값은 접근 가능한 POP+PMP 합산이며 위젯 안에서 개별 서버로 전환한다.
- `CC 로그 조회`는 채널 검색 후 메시지 목록과 Audit을 단계적으로 확인하는 화면이고, `MessageID 조회`는 이미 알고 있는 Message ID의 Audit을 바로 조회하는 화면이다.
- `리소스 조회`는 CPU·Memory·Queue·Thread의 현재 상태를 확인하므로 `현황` 카테고리에 둔다.
- 채널 기준정보 drill-down 메뉴는 `시스템 별 채널 정보`로 표시한다.
- 대시보드 최초 진입에서는 summary, channel, alert와 각 위젯 API를 서로 기다리지 않고 독립 호출한다. 응답이 먼저 끝난 영역부터 로딩 상태를 실제 데이터로 교체한다.
- 대시보드가 mount된 동안 `DASHBOARD_REFRESH_INTERVAL_MS` 기준 15분마다 재조회한다. 백그라운드 갱신에서는 기존 데이터를 비우거나 페이지를 이동하지 않고 성공한 API의 데이터만 교체한다.
- 일부 API가 실패해도 다른 위젯의 응답과 기존 cache를 지우지 않는다. SID가 변경될 때만 새 SID의 최초 로딩 상태를 적용한다.
