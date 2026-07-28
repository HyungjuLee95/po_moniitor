# Collectors MANUAL
작은 시간 window, 중복 안전 upsert, 실행 잠금, 성공 범위 checkpoint를 기본으로 한다. 현재 잠금은 API 프로세스 내부 SID 단위이며 다중 인스턴스 운영 전 PostgreSQL advisory lock으로 확장한다. 조회 결과는 건수와 checkpoint를 저장하고 메시지 원문은 PostgreSQL에 복제하지 않는다.
