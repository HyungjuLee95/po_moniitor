# Git 작업 규칙

- 기본 브랜치: `main`
- 기능: `feature/<domain>-<summary>`
- 수정: `fix/<domain>-<summary>`
- 문서: `docs/<summary>`

커밋은 Conventional Commits 형식을 사용합니다.

```text
feat(monitoring): add server summary endpoint
fix(auth): reject inactive accounts
docs(configuration): document server onboarding
```

커밋 전 `npm run lint`, `npm test`, Python 테스트를 수행합니다. `.env`, 인증서, 덤프, 운영 로그는 커밋하지 않습니다. 사내 원격 저장소 연결은 README의 명령을 따릅니다.
