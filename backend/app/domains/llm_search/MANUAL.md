# LLM Search MANUAL
`LLM_API_URL`이 비어 있으면 설정 안내 JSON을 반환하고, 값이 있으면 provider adapter가 JSON POST를 수행한다. URL은 백엔드 `.env`에만 두며 frontend bootstrap이나 오류 응답에 포함하지 않는다.

전송 context는 `id`, `sid`, `title`, `detail`, `domain`, `severity`, `status`, 발생 시각 allowlist만 허용한다. payload·token·credential과 그 밖의 임의 필드는 전달하지 않는다. provider 응답은 `answer`, `sources`, `confidence` JSON 객체여야 하며 규격 불일치는 `502`로 처리한다.
