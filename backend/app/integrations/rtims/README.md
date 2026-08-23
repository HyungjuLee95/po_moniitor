# RTIMS Oracle Integration
기존 HYNIXRTIMS schema를 읽어 대시보드 통계, 최근 메시지, 채널 상태, 리소스·Queue와 장애를 제공한다. 신규 PostgreSQL과 역할이 다르며 데이터 마이그레이션을 하지 않는다. PostgreSQL `rtims` schema는 로컬·오프라인 호환 및 계약 검증용이다.

실시간 화면의 live 원본은 Collector buffer가 아니라 `MON_MSG_LOG`와 `MON_INTF_MAP`이다. 리소스는 `MON_RES_USAGE`/`MON_RESOURCE`, 장애는 `MON_ERR_HIST`, 시스템 대기는 `MON_Q_STATUS`를 사용한다. `MON_BUF_AAE_MSG` 기반 구형 서비스와 `MON_INCI_LOG`는 현재 API 계약에 사용하지 않는다.

필수 객체·컬럼의 단일 코드는 `contract.py`, 설치 로직은 `schema_setup.py`다. PostgreSQL DDL은 `backend/migrations/006_rtims_compatibility.sql`, Oracle DDL은 `backend/oracle/001_rtims_monitoring_schema.sql`에 있다. DDL은 현재 API가 요구하는 14개 객체만 다루며 Collector 전체 schema·procedure·job을 생성하지 않는다.
