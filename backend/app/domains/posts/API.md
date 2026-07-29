# Posts API

| Method | Path | Permission |
|---|---|---|
| GET | `/api/v1/posts` | `posts:read` |
| POST | `/api/v1/posts` | `posts:write` |
| PUT | `/api/v1/posts/{post_id}` | `posts:write`, 작성자 또는 ADMIN |
| DELETE | `/api/v1/posts/{post_id}` | `posts:write`, 작성자 또는 ADMIN |
