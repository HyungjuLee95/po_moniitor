# ADR-002 RTIMS Collector 저장소는 Oracle로 유지

## 상태

승인

## 날짜

2026-08-28

## 배경

기존 RTIMS Collector는 SAP PO HANA의 AAE 메시지를 Oracle buffer에 적재한 뒤 `process_msg_logs`로 운영 조회 테이블을 가공한다. 새 웹 애플리케이션은 PostgreSQL을 사용하지만 Collector까지 PostgreSQL로 바꾸면 검증된 Oracle 프로시저·조회 계약과 이중화되며 기존 RTIMS 화면과 데이터가 갈라진다. 여러 SAP PO 서버는 HANA host·schema·계정이 서로 다를 수 있다.

## 결정

- 사용자·권한·개인 설정·웹 cache는 PostgreSQL에 둔다.
- RTIMS Collector buffer, 가공, runtime checkpoint와 실행 로그는 기존 Oracle schema를 단일 원본으로 유지한다.
- 서버별 HANA 연결과 BE/EO profile은 `.env`의 `PO_SERVERS_JSON[].collectors`에서 독립 설정한다.
- HANA 조회는 `(timestamp, message_id)` 안정 경계와 bounded TOP을 사용한다.
- `MON_BUF_AAE_MSG` 적재, `process_msg_logs`, `MON_COLLECTOR_PARAMS` checkpoint, `MON_COLLECTOR_LOG` 성공 기록은 한 Oracle transaction이다.
- 자동 실행은 opt-in이고 서버·profile을 순차 처리한다. 분산 잠금 전에는 scheduler backend를 한 인스턴스로 제한한다.

## 검토한 대안

1. Collector도 PostgreSQL로 재구현: 운영 구조는 단순해지지만 기존 Oracle 프로시저·RTIMS 조회 계약을 모두 다시 구현하고 결과 일치성을 검증해야 한다.
2. 서버별 Collector 프로세스를 별도 배포: 장애 격리는 좋지만 배포·설정·관측 대상이 서버 수만큼 늘어난다.
3. 중앙 backend의 Oracle Collector profile: 기존 저장 계약을 유지하면서 서버별 source 설정과 bounded 순차 실행을 한 곳에서 관리할 수 있다.

## 결과

- 장점: 기존 RTIMS 데이터·프로시저·조회 화면과 동일한 Oracle 원본을 사용하고 PostgreSQL 역할이 명확해진다.
- 비용과 단점: Oracle write 권한과 전체 Collector schema가 필요하며 한 backend 프로세스 잠금만으로는 active-active scheduler를 지원하지 않는다.
- 후속 작업: 사내 HANA/Oracle smoke test, 프로시저 의존 객체 검증, 다중 backend가 필요할 때 Oracle 분산 lock 도입.

## 관련 문서와 코드

- [`../../backend/app/domains/collectors/MANUAL.md`](../../backend/app/domains/collectors/MANUAL.md)
- [`../../backend/app/integrations/rtims/MANUAL.md`](../../backend/app/integrations/rtims/MANUAL.md)
- [`../../backend/app/integrations/sap_po/hana_collector.py`](../../backend/app/integrations/sap_po/hana_collector.py)
- [`../../backend/app/integrations/rtims/collector_repository.py`](../../backend/app/integrations/rtims/collector_repository.py)
