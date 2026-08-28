# Auth ERROR

## 2026-08-23 / Administrator 안내 렌더 테스트의 마크업 경계 오판

- 증상: 화면에는 안내가 보이지만 운영 렌더 테스트가 `Administrator 계정은...` 연속 문자열을 찾지 못해 실패했다.
- 영향: Next.js build는 성공했고 테스트 assertion만 실패했다.
- 원인: `Administrator`를 `<b>`로 강조해 HTML 태그가 두 텍스트 사이에 존재하는데 테스트가 연속 plain text를 가정했다.
- 해결: Administrator와 나머지 안내 문구를 독립적으로 검사하도록 assertion을 분리했다.
- 검증: 수정 후 `npm run lint`와 `npm test`를 통과했다.
- 재발 방지: 서버 렌더 HTML 검증은 의미 단위 텍스트를 확인하고 표현용 태그 경계를 고정하지 않는다.
- 관련 파일: `frontend/tests/rendered-html.test.mjs`, `LoginPage.tsx`

반복 로그인 실패는 API base URL, backend CORS, credential, token 저장을 확인한다.
