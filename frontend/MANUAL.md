# Frontend MANUAL

- 컴포넌트와 상태는 소유 도메인 안에 둔다.
- 여러 도메인이 공유하는 API·세션·타입만 `src/core`에 둔다.
- 페이지는 도메인을 조립하며 업무 로직을 직접 가지지 않는다.
- 새 위젯은 dashboard registry에 등록하고 기본 layout과 backend validation을 함께 수정한다.
- 사용자 저장값은 backend API가 원본이며 localStorage는 장애 시 보조값이다.
- 반응형, 키보드 접근성, reduced motion을 유지한다.
- 각 도메인의 `API.md`에 화면별 호출, 권한, 로딩·오류·다운로드·SSE 처리 계약을 기록한다.
- 화면 검증 오류는 해당 도메인의 `ERROR.md`, 여러 화면에 공통인 오류는 frontend 또는 루트 `ERROR.md`에 기록한다.
