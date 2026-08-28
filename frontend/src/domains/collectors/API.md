# Collectors API

상태는 `GET /collectors`, 수동 실행은 `POST /collectors/run`을 사용한다. Oracle profile 응답은 `collector_id`, `oracle_instance_id`, `delivery_semantics`, Oracle checkpoint와 최신 실행 정보를 포함한다. 단일 profile 실행은 `{ "sids": ["SID"], "collector_ids": ["profile-id"] }`를 전송한다.
