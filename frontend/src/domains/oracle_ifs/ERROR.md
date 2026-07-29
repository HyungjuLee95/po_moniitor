# Oracle IFS ERROR

빈 목록은 동기화 시각, 사용자 ID 매핑, Oracle 연결과 PostgreSQL migration을 확인한다.

## 2026-07-28 / 초기 조회 effect의 동기 상태 변경 lint 오류

- 증상: React lint가 effect 내부의 즉시 `load()` 호출을 `set-state-in-effect`로 차단
- 영향: production build는 성공했지만 lint 검증 실패
- 원인: 비동기 함수 호출이 effect 본문에서 바로 시작되어 React 19 규칙이 동기 상태 변경 가능성으로 판정
- 해결: 0ms timer에서 조회를 시작하고 cleanup에서 timer를 해제
- 검증: frontend lint 통과, production build 및 rendered HTML test 통과
- 재발 방지: 초기 API 조회는 프로젝트의 timer cleanup 패턴을 사용
