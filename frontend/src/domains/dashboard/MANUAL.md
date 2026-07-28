# Dashboard MANUAL

- 전체 메뉴는 화면에 고정하지 않고 좌측 상단 메뉴 버튼으로 여는 drawer를 사용한다.
- 메뉴 선택, 닫기 버튼, 배경 클릭, `Escape` 입력으로 drawer를 닫을 수 있어야 한다.
- 평균 응답시간의 원본 API 필드는 millisecond를 유지하되 화면은 초 단위 소수점 셋째 자리(`0.000초`)로 표시한다.
새 위젯은 `WidgetId`, registry, 기본 layout, backend validator에 등록한다. 사용자 설정은 API가 원본이고 localStorage는 보조 복구값이다.
