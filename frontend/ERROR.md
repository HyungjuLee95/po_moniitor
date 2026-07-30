# Frontend ERROR

## 2026-07-30 / 비공식 Next 호환 런타임으로 인한 실행 환경 불일치

- 증상: 프로젝트가 Next.js 구조를 사용하면서도 실행·빌드는 Vinext/Vite/Cloudflare Worker 호환 계층에 의존해 공식 Next.js 환경에서 오류가 발생했다.
- 영향: 사내 이식 환경에서 표준 Next.js 실행 명령과 빌드 결과를 그대로 사용할 수 없었다.
- 원인: 초기 프론트 템플릿의 호환 런타임 설정과 Worker 렌더 테스트가 남아 있었다.
- 해결: 실행 명령을 `next dev/build/start`로 교체하고 공식 `next.config.ts`와 Next 서버 기반 렌더 테스트로 전환했다. Vinext/Vite/Worker/Sites 전용 파일과 패키지는 제거했다.
- 검증: `npm run lint`, `npm test`, `npm audit --omit=dev`, 로컬 HTTP 응답 검증.
- 재발 방지: `SKILL.md` 완료 조건에 공식 Next CLI와 비공식 호환 런타임 부재 확인을 추가했다.
- 관련 파일 또는 명령: `frontend/package.json`, `frontend/next.config.ts`, `frontend/tests/rendered-html.test.mjs`

## 2026-07-30 / Next.js 전환 중 운영 의존성 보안 검증 실패

- 증상: Next.js 16.2.6 및 16.2.12 기본 의존성 조합에서 `npm audit --omit=dev`가 PostCSS와 sharp 고위험 경고를 반환했다.
- 영향: 기능 실행에는 즉시 문제가 없었지만 운영 빌드의 의존성 보안 기준을 통과하지 못했다.
- 원인: Next.js가 취약점 수정 이전 버전의 PostCSS와 sharp를 직접 포함했다.
- 해결: Next.js 최신 안정 버전 16.2.12를 사용하고 `overrides`로 PostCSS 8.5.25와 sharp 0.35.3을 고정했다.
- 검증: `npm audit --omit=dev` 결과 `found 0 vulnerabilities`, `npm ls postcss sharp`에서 override 적용 확인.
- 재발 방지: 패키지 변경 시 운영 의존성 audit와 공식 Next 빌드를 함께 실행한다.
- 관련 파일 또는 명령: `frontend/package.json`, `frontend/package-lock.json`

## 2026-07-30 / standalone 빌드와 next start 실행 계약 불일치

- 증상: 첫 공식 Next 렌더 테스트는 통과했지만 `output: "standalone"` 설정에서는 `next start`를 사용할 수 없다는 경고가 발생했다.
- 영향: 문서와 package script에 기재한 운영 실행 명령이 실제 빌드 설정과 맞지 않았다.
- 원인: 표준 `next start`를 사용하면서 배포 서버용 standalone 출력을 동시에 지정했다.
- 해결: 별도 standalone 서버 패키징 요구가 없으므로 `output` 설정을 제거하고 표준 Next 빌드와 `next start` 계약으로 통일했다.
- 검증: 설정 변경 후 `npm test`와 `npm run start` HTTP 응답 확인.
- 재발 방지: 빌드 output 변경 시 운영 시작 명령과 설치 문서를 함께 검증한다.
- 관련 파일 또는 명령: `frontend/next.config.ts`, `frontend/package.json`

## 2026-07-28 / Fetch did not settle during external integration delays

- Symptom: asynchronous loading states remained visible for an excessive time.
- Impact: local previews without SAP PO or RTIMS connectivity did not transition to usable fallback states.
- Cause: common `apiRequest` did not define a network timeout.
- Resolution: added an `AbortController`-based 30-second default and a dashboard-specific 12-second timeout.
- Verification: lint, build, render test, and browser dashboard loading-state verification.
- Prevention: external-integration UI callers must set an appropriate `timeoutMs`.
- Related: `frontend/src/core/api.ts`

프론트 공통 오류를 MANUAL의 오류 형식으로 기록한다. API 불일치, hydration, 반응형, 접근성, 사용자 설정 복구 문제는 관련 도메인 ERROR에도 기록한다.
