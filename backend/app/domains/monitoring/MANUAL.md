# Monitoring MANUAL
registry의 `monitor` capability를 확인하고 SAP/RTIMS 원본을 화면 DTO로 변환한다. 데이터 기준 시각과 수집 시각을 구분한다.

응답시간 API 값은 밀리초 계약을 유지하고 프론트에서 초로 변환해 `0.000초` 형식으로 표시한다. 대시보드 평균과 지연 목록은 `configuration.monitoring_policy`의 동일한 window·threshold를 사용한다. 평균과 지연 원본은 `MON_MSG_LOG`의 `REQ_ELAPSED_SEC + PROV_ELAPSED_SEC + RES_ELAPSED_SEC`이며 화면 표시 전 밀리초로 변환한다. RTIMS 실제 코드값과 집계 단위는 사내망에서 smoke test한다.
