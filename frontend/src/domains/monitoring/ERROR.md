# Monitoring ERROR

## 2026-07-28 / 트래픽 위젯의 effect 내부 동기 상태 갱신

- 증상: frontend lint에서 `react-hooks/set-state-in-effect` 오류가 발생했다.
- 원인: 조회 가능한 서버가 없을 때 effect 본문에서 `setRows`, `setNotice`를 즉시 호출했다.
- 해결: 빈 서버 목록도 비동기 조회 결과 처리 경로에서 빈 bucket과 안내 문구를 설정하도록 통합했다.
- 검증: frontend lint, production build, rendered HTML 테스트가 모두 통과했다.
- 예방: effect의 상태 갱신은 외부 작업의 callback에서 수행하고 파생 가능한 값은 렌더 단계에서 계산한다.

지표 불일치는 API DTO, formatter, timezone과 선택 SID를 확인한다.
