# Collectors ERROR
정체·공백은 실행 잠금, 마지막 오류, checkpoint 원자성, SAP rate limit 순으로 확인한다.

## 2026-08-28 / 수동 API만 있고 자동 Collector 수명주기 없음

- 증상: Collector capability와 수동 실행 API가 있어도 backend 시작 후 수집이 자동으로 실행되지 않았다.
- 영향: 운영자가 수동 API를 호출하지 않으면 checkpoint가 갱신되지 않았다.
- 원인: Collector 도메인에 환경 변수 스위치와 시작·종료 수명주기, 고정 지연 scheduler가 없었다.
- 해결: 기본 OFF인 `RTIMS_COLLECTOR_ENABLED`와 시작 지연·간격·조회 상한을 추가하고 FastAPI lifespan에서 전용 daemon thread를 시작·종료한다.
- 검증: 서버 capability 필터, SID 실패 격리, 시작 지연과 고정 지연의 중단 가능 대기를 단위 테스트한다. 실제 SAP·DB 연결은 수행하지 않는다.
- 재발 방지: 자동 작업은 opt-in, bounded limit, 순차 실행, 종료 event와 실행 범위를 도메인 문서에 함께 정의한다.
- 관련 파일: `.env.example`, `backend/app/core/config.py`, `backend/app/main.py`, `backend/app/domains/collectors/scheduler.py`.

## 2026-08-28 / Oracle 수집 경로와 PostgreSQL 상태 원본 불일치

- 증상: HANA 메시지를 Oracle에 적재하도록 전환해도 Collector 상태 API는 PostgreSQL `monitoring.collector_checkpoint`만 읽었다.
- 영향: 실제 Oracle checkpoint와 화면 상태가 달라져 정상 수집을 정체로 오판할 수 있었다.
- 원인: 초기 수동 Collector 호환 경로의 상태 repository를 Oracle profile에도 그대로 사용했다.
- 해결: Oracle profile은 `MON_COLLECTOR_PARAMS`의 `TIMESTAMP/MESSAGE_ID`와 `MON_COLLECTOR_LOG` 최신 실행을 조회하고, profile 없는 서버만 PostgreSQL 호환 상태를 사용한다.
- 검증: fake Oracle cursor로 checkpoint·최신 로그·처리 건수 변환 계약을 테스트한다.
- 재발 방지: 수집 write 원본과 상태 read 원본을 같은 profile 계약에서 변경한다.

## 2026-08-28 / PO_SERVERS_JSON 검증 테스트의 lazy property 누락

- 증상: 중복 `oracle_instance_id`를 넣은 설정 테스트가 예외 없이 끝났다.
- 영향: 설정 자체 생성만으로는 lazy `po_servers` property 검증이 실행되지 않아 잘못된 테스트 결과가 날 수 있었다.
- 원인: 테스트가 `Settings` 생성만 하고 `.po_servers`를 읽지 않았다.
- 해결: 테스트에서 property를 명시적으로 평가하고 전역 instance ID 중복을 검증한다.
- 검증: 설정·scheduler·Oracle 계약 테스트가 통과한다.
- 재발 방지: JSON 파생 설정의 validation 테스트는 실제 파생 property까지 평가한다.
