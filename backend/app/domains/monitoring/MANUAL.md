# Monitoring MANUAL
registry의 `monitor` capability를 확인하고 SAP/RTIMS 원본을 화면 DTO로 변환한다. 데이터 기준 시각과 수집 시각을 구분한다.

응답시간 API 값은 밀리초 계약을 유지하고 프론트에서 초로 변환해 `0.000초` 형식으로 표시한다. 대시보드 평균과 지연 목록은 `configuration.monitoring_policy`의 동일한 window·threshold를 사용한다. 평균과 지연 원본은 `MON_MSG_LOG`의 `REQ_ELAPSED_SEC + PROV_ELAPSED_SEC + RES_ELAPSED_SEC`이며 화면 표시 전 밀리초로 변환한다. RTIMS 실제 코드값과 집계 단위는 사내망에서 smoke test한다.

메시지 트래픽은 `MON_MSG_LOG`의 `REQ_START_DTM`을 기준으로 집계한다. 시간 모드는 오늘 `00:00:00~23:59:59`를 24개 시간 bucket으로, 일 모드는 오늘을 포함한 지정 일수를 날짜 bucket으로 묶는다. 메시지 크기는 요청·응답 크기의 합계이며 null은 0으로 취급한다. 날짜 경계는 RTIMS Oracle 서버의 `sysdate`를 기준으로 한다.

POP+PMP 전체 보기는 멀티 SID를 한 요청에서 우회 처리하지 않는다. 프론트가 사용자에게 접근 허용된 각 SID를 호출하므로 `require_server_access`가 서버마다 적용된다. 일부 서버 실패 시 성공한 서버만 합산하고 화면에 부분 실패를 표시한다.

대시보드 summary는 `failed_messages`와 `pending_messages`를 별도 필드로 제공한다.
