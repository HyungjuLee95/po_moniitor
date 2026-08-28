# Collectors
서버별 HANA AAE 메시지를 증분 조회해 기존 RTIMS Oracle buffer와 가공 프로시저에 연결한다. Oracle profile이 없는 서버에는 기존 SAP PO 조회·PostgreSQL checkpoint 호환 경로를 유지한다. 자동 실행은 `RTIMS_COLLECTOR_ENABLED`가 켜진 경우에만 FastAPI 수명주기와 함께 동작한다.

Collector는 백그라운드 기반 기능이며 전역 메뉴 대신 admin 환경 설정의 수집 상태 탭에서 노출한다.

Oracle profile 경로는 `HANA bc_msg/bc_msg_log + Oracle Pending ID 상태 재조회 -> MON_BUF_AAE_MSG -> process_msg_logs -> MON_COLLECTOR_PARAMS/LOG` 순서다. buffer 적재, 프로시저, `(TIMESTAMP, MESSAGE_ID)` checkpoint, 성공 로그는 한 Oracle transaction으로 처리한다. PostgreSQL은 이 경로의 checkpoint 원본이 아니며 사용자·권한·개인 설정을 계속 담당한다.

현재 잠금은 한 backend 프로세스 안의 `(SID, collector_id)` 단위다. Collector scheduler를 실행하는 backend 인스턴스는 하나만 허용하며 다중 backend 동시 실행 전에는 Oracle 분산 잠금 계약을 추가해야 한다.
