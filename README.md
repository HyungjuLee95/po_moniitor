# PO_MONITOR_MAIN

SAP PO API Directory를 이용하는 통합 모니터링 프로젝트입니다. 프론트엔드는 React 19.2.7, 백엔드는 Python 3.11.7/FastAPI, 운영 데이터는 PostgreSQL을 기준으로 설계했습니다.

## 시작하기

```powershell
Copy-Item .env.example .env
npm install
npm run dev
```

별도 터미널에서 백엔드를 실행합니다.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
uvicorn app.main:app --app-dir backend --reload --port 8000
```

초기 화면은 데모 모드이며 `.env`의 `DEMO_ADMIN_USERNAME`과 `DEMO_ADMIN_PASSWORD`로 로그인합니다. 실운영 전에는 `DEMO_MODE=false`, 강력한 `SECRET_KEY`, PostgreSQL 계정과 실제 SAP PO 접속 정보를 설정해야 합니다.

## 서버 자동 반영

`.env`의 `PO_SERVERS_JSON`에 서버 객체를 추가하고 백엔드를 재시작하면 됩니다. 백엔드가 SID·환경·포트·기능을 검증하고 `/api/v1/configuration/bootstrap`에 공개 가능한 값만 내려주므로 프론트 서버 선택 목록에 자동 반영됩니다. `base_url`과 SAP 계정 정보는 브라우저에 전달되지 않습니다.

상세 규칙은 [docs/ENVIRONMENT.md](docs/ENVIRONMENT.md), 전체 구조는 [PROJECT.md](PROJECT.md)를 참고하세요.

## 검증 명령

```powershell
npm run lint
npm test
python -m compileall backend\app backend\tests
```

## Git 원격 저장소 연결

현재 폴더는 독립 Git 저장소로 초기화되어 있습니다. 사내 Git URL을 받은 뒤 아래처럼 연결합니다.

```powershell
git remote add origin <사내-Git-저장소-URL>
git add .
git commit -m "feat: initialize PO Monitor Main"
git branch -M main
git push -u origin main
```

비밀값이 든 `.env`는 커밋하지 말고 `.env.example`만 공유합니다.
