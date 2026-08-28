# Collectors ERROR
정체 표시는 backend status, checkpoint 시각과 polling을 확인한다.

## 2026-08-28 / 한 SID의 다중 profile 카드 충돌

- 증상: 같은 서버의 BE/EO profile 카드가 같은 React key를 사용하고 단일 실행 버튼이 두 profile을 모두 실행했다.
- 원인: 기존 상태 계약이 SID당 checkpoint 하나만 전제했다.
- 해결: 카드 key와 수동 실행을 `(sid, collector_id)` 단위로 변경하고 Oracle profile 정보를 표시한다.
- 검증: frontend lint·build와 rendered HTML 테스트에서 설정 화면을 확인한다.
