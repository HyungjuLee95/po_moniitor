# Dashboard ERROR

## 2026-07-28 / Dashboard remained in loading state

- Symptom: KPI, traffic, system result, Queue, live interface, daily check, and alert widgets kept showing loading states.
- Impact: A local preview without SAP PO or RTIMS connectivity could not display the dashboard.
- Cause: Requests were independent, but browser fetches had no maximum wait time, so `finally` never ran while an external backend call remained pending.
- Resolution: Added a cancellable common request timeout and a 12-second dashboard request limit.
- Verification: Confirmed in the browser that every loading state settles independently after the request limit.
- Prevention: Every new dashboard API must use `DASHBOARD_REQUEST_TIMEOUT_MS` and preserve a safe fallback or the last successful value.
- Related: `frontend/src/core/api.ts`, `frontend/src/core/refresh.ts`
설정 복원 실패는 payload validation, API 응답, localStorage JSON, widget registry 동기화를 확인한다.
