# 프로젝트 ERROR

공통 또는 여러 도메인에 영향을 주는 오류 이력을 기록한다. 도메인 내부 오류는 해당 도메인의 `ERROR.md`가 원본이다.

## 2026-07-28 / Windows Git 저장소 소유권 불일치

- 증상: `detected dubious ownership`
- 원인: Codex 샌드박스 계정과 사용자 계정의 Windows SID가 다름
- 해결: 해당 저장소 경로만 `safe.directory`로 등록
- 재발 방지: 새 저장소 생성 후 사용자 계정에서 Git 상태를 확인
