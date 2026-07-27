# Configuration 작업 규칙

서버 속성 변경은 `PoServer` 모델, `.env.example`, `ENVIRONMENT.md`를 함께 수정한다. 비밀 필드는 `public_view()`에 추가하지 않는다. 새 capability는 타입, 권한, 실제 endpoint 검사를 함께 갱신한다.
