# Dashboard MANUAL
운영 모드는 `iam.dashboard_preference`의 JSONB가 원본이다. widget registry나 View ID 변경 시 frontend 기본 layout과 backend 허용 목록을 동시에 수정한다. 이전 JSON에는 누락된 신규 위젯을 추가하고 기본 비표시 위젯을 보정해 하위 호환한다.
