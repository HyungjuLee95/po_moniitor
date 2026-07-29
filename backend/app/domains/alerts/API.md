# Alerts API

`GET /api/v1/alerts?sid=`는 `alerts:read`, `PATCH /api/v1/alerts/{id}/acknowledge`는 `alerts:acknowledge` 권한을 사용한다. RTIMS 인시던트를 알림 DTO로 변환하며 acknowledge 영속화는 후속 Alert Inbox 원본 연결이 필요하다.
