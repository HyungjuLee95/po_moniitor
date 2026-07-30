# Frontend

공식 Next.js 16.2.12 App Router와 React 19.2.7 기반 운영 콘솔이다. `app`은 렌더링 진입점, `src/app`은 애플리케이션 조립, `src/core`는 전역 계약, `src/domains`는 업무 기능을 담당한다.

프론트 런타임은 Next.js 공식 CLI(`next dev`, `next build`, `next start`)를 사용한다. Vinext, Vite, Cloudflare Worker 호환 계층은 사용하지 않는다. 프로젝트 루트의 `.env`는 `next.config.ts`에서 읽으며, 브라우저에 공개해도 되는 값만 `NEXT_PUBLIC_` 접두사를 사용한다.

| 도메인 | 책임 |
|---|---|
| auth | 로그인 화면과 세션 |
| dashboard | 위젯 registry, 배치, 개인 설정, 자주 사용하는 메뉴 |
| server | 서버 선택 표시 계약 |
| monitoring | 실제 24시간 트래픽, 실시간 인터페이스, 시스템 처리·Queue 시각화 |
| channels | 채널 상태·제어·채널별 통계 |
| messages | 최근 메시지와 Message ID Audit |
| interfaces | 시스템별 채널과 topology |
| incidents | 장애 관리 |
| collectors | 환경 설정 하위 Collector 상태 |
| workspaces | 프로젝트 작업과 단계 진행 |
| settings | 연결·모니터링 기준·사용자 권한·수집 상태 |
| alerts | 상단 점멸 알림과 목록 |
| llm_search | 장애 원인 검색 UI |
| hrd | HRD 인터페이스·Excel·테스트 메시지·일일 점검 |
| oracle_ifs | Oracle IFS 동기화와 이관 일정 |
| posts | 운영 지식 게시글 |

작업 전 `MANUAL.md`, `SKILL.md`, 대상 도메인의 다섯 문서를 읽는다. `API.md`는 화면이 사용하는 백엔드 계약의 소비자 문서다.

## 실행 명령

```powershell
cd D:\toyproject\PO_MONITOR_MAIN\frontend
npm install
npm run dev
```

검증과 운영 빌드:

```powershell
npm run lint
npm test
npm run build
npm run start
```

`npm test`는 공식 Next.js 운영 빌드를 만든 뒤 실제 Next 서버를 임시 포트로 실행하여 렌더링 결과를 검사한다.
