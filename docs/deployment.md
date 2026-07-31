# 사내 배포와 롤백

상세 설치·인증서·오프라인 패키지 준비는 [`INSTALL_INTERNAL_NETWORK.md`](INSTALL_INTERNAL_NETWORK.md)를 따른다.

## 환경

| 환경 | 목적 | 데이터 | 접근 권한 |
|---|---|---|---|
| Local | 기능 개발과 mock/demo | 비운영 | 개발자 |
| Internal Test | SAP PO·RTIMS 통합 검증 | 제한된 사내 데이터 | 승인된 개발·운영자 |
| Production | 실제 모니터링과 운영 작업 | 운영 데이터 | 최소 권한 사용자 |

## 배포 전 확인

- [ ] Python 3.11.7, Node 22.13.0 이상, npm 11.13.0 확인
- [ ] `python scripts/validate_project_docs.py` 통과
- [ ] Backend pytest 통과
- [ ] Frontend lint·build·render test·운영 audit 통과
- [ ] `.env` 비밀값과 허용 CORS·서버 registry 검토
- [ ] 순번별 PostgreSQL migration과 백업 확인
- [ ] SAP PO·RTIMS·선택 외부 시스템 연결 점검
- [ ] rollback 대상 이전 버전과 DB 호환성 확인

## 배포 절차

1. 승인된 Git commit 또는 사내 반입본을 준비한다.
2. `.env.example`을 기준으로 운영 서버의 기존 `.env`를 검토한다.
3. 새 migration만 번호 순서대로 적용한다.
4. Backend를 시작하고 `/health`와 OpenAPI route를 확인한다.
5. Frontend production build를 만들고 `npm run start`로 시작한다.
6. 역할별 핵심 조회와 허용된 운영 작업 한 건을 smoke test한다.
7. 오류율·응답 시간·외부 연동 로그를 확인한다.

## 배포 후 smoke test

- [ ] ADMIN 로그인과 사용자·환경 메뉴 접근
- [ ] OPERATOR·VIEWER 메뉴 및 backend 권한 차이
- [ ] 서버 목록과 서버 범위
- [ ] 대시보드 widget별 독립 응답
- [ ] 채널 검색·메시지 목록·CC 로그
- [ ] 시스템별 채널 정보
- [ ] HRD 선택 조회
- [ ] RTIMS 리소스·Queue·장애
- [ ] 허용된 테스트 채널의 제어 또는 dry-run

## 롤백

1. 운영 영향과 중단 기준을 판단한다.
2. 신규 프로세스를 중지하고 이전 정상 commit의 backend/frontend를 재배포한다.
3. migration이 하위 호환인지 확인한다. 데이터 rollback이 필요하면 사전 백업과 별도 승인 절차를 사용한다.
4. health와 핵심 조회를 다시 확인한다.
5. 영향·원인·복구 결과를 루트 또는 관련 도메인 `ERROR.md`와 `CHANGELOG.md`에 기록한다.
