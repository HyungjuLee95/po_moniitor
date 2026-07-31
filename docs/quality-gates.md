# 품질 게이트

## 자동 검사

- 루트·영역·도메인 필수 문서 존재
- 모든 frontend/backend 실제 도메인의 `PROJECT.md`·`SKILL.md` 색인
- 로컬 Markdown 링크 대상 존재와 프로젝트 루트 탈출 방지
- `.env`, private key 등 민감 파일의 Git 추적 방지
- Frontend lint·production build·render test·운영 의존성 audit
- Backend pytest

## 완료 차단 조건

- 사용자 요청과 수용 기준 미충족
- 관련 테스트 실패
- API·권한·외부 원본 변경 후 `API.md` 갱신 누락
- 신규 도메인 문서 또는 색인 누락
- 문서와 코드가 서로 다른 동작을 설명
- 검증 실패를 관련 `ERROR.md`에 기록하지 않음
- 수행하지 않은 검증을 통과로 보고
- 비밀값·내부 URL·원본 payload 노출 가능성

## 문서 검사

```powershell
python scripts\validate_project_docs.py
```

검사 범위는 다음과 같다.

- 루트 문서
- `frontend`, `backend` 영역 문서
- `frontend/src/domains/*`, `backend/app/domains/*`의 5개 문서
- `PROJECT.md`, `SKILL.md` 도메인 색인
- 로컬 Markdown 링크
- Git이 추적하는 민감 파일명

## 수동 확인

- 실제 사용자 역할별 메뉴와 backend 권한
- SAP PO·RTIMS 필드·상태 코드·시간 및 크기 단위
- 대량 변경 preview·실행·부분 실패·감사 결과
- 사내 인증서·프록시·오프라인 설치
- 배포 후 핵심 흐름 smoke test와 rollback 가능 여부

## 문서 건강검진

마일스톤 완료 시 코드·테스트·문서·도메인 색인·링크·상태를 비교한다. 완료된 `CURRENT_TASK.md`는 안정 문서에 필요한 내용만 반영하고 `IDLE`로 정리한다.
