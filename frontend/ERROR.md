# Frontend ERROR

## 2026-07-28 / Fetch did not settle during external integration delays

- Symptom: asynchronous loading states remained visible for an excessive time.
- Impact: local previews without SAP PO or RTIMS connectivity did not transition to usable fallback states.
- Cause: common `apiRequest` did not define a network timeout.
- Resolution: added an `AbortController`-based 30-second default and a dashboard-specific 12-second timeout.
- Verification: lint, build, render test, and browser dashboard loading-state verification.
- Prevention: external-integration UI callers must set an appropriate `timeoutMs`.
- Related: `frontend/src/core/api.ts`

프론트 공통 오류를 MANUAL의 오류 형식으로 기록한다. API 불일치, hydration, 반응형, 접근성, 사용자 설정 복구 문제는 관련 도메인 ERROR에도 기록한다.
