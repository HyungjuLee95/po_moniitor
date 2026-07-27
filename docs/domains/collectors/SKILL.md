# Collectors 작업 규칙

작은 시간 window, checkpoint, 중복 안전 upsert를 기본으로 한다. 병렬 실행 잠금을 두고 성공한 범위만 checkpoint로 확정한다. SAP PO 부하를 줄이기 위해 페이지 크기와 호출 간격을 설정 가능하게 한다.
