# 사내망 설치 및 이식 가이드

이 문서는 `PO_MONITOR_MAIN` 소스 전체를 사내 PC 또는 서버로 복사한 뒤 설치하는 절차다. 실제 SAP PO·RTIMS·PostgreSQL 접속값은 외부 PC에서 만들지 않고 사내망에서 `.env`에 입력한다.

## 1. 같이 가져갈 파일

가장 안전한 방법은 프로젝트 루트 전체를 복사하되 아래의 제외 항목만 빼는 것이다. 주요 필수 항목은 다음과 같다.

```text
PO_MONITOR_MAIN/
├─ backend/
│  ├─ app/
│  ├─ tests/
│  ├─ migrations/001_initial.sql
│  ├─ migrations/002_dashboard_alert_llm.sql
│  ├─ migrations/003_workspaces.sql
│  ├─ migrations/004_monitoring_policy_and_iam.sql
│  ├─ migrations/005_required_feature_domains.sql
│  ├─ requirements.txt
│  └─ requirements-dev.txt
├─ frontend/
│  ├─ app/
│  ├─ public/
│  ├─ src/
│  ├─ tests/
│  ├─ package.json
│  ├─ package-lock.json
│  ├─ tsconfig.json
│  ├─ vite.config.ts
│  └─ eslint.config.mjs
├─ docs/
├─ .env.example
├─ start-backend.bat
└─ start-frontend.bat
```

가져가지 않아도 되는 항목:

```text
.git/
node_modules/
dist/
frontend/node_modules/
frontend/build/
frontend/dist/
frontend/.wrangler/
.vite/
.wrangler/
.env
__pycache__/
backend/.pytest_cache/
work-dev.stdout.log
work-dev.stderr.log
```

`.env`는 접속정보 유출을 방지하기 위해 복사본에 포함하지 않는다. 사내망에서 `.env.example`을 `.env`로 복사한 뒤 실제 값을 입력한다.

## 2. 사내 PC에 설치할 프로그램

| 프로그램 | 요구 버전 | 용도 |
|---|---:|---|
| Python x64 | 3.11.7 | FastAPI 백엔드 |
| Node.js x64 | 22.13.0 이상 | React 빌드와 실행 |
| npm | 11.13.0 | 프론트 패키지 설치 |
| PostgreSQL | 17 권장 | 사용자·권한·개인 설정·checkpoint |
| Git | 선택 | 사내 Git 저장소를 사용할 때 |
| Oracle Instant Client | 조건부 | 사내 Oracle 버전 또는 인증 방식이 python-oracledb Thin 모드를 지원하지 않을 때 |

설치 확인:

```powershell
python --version
node --version
npm --version
psql --version
```

npm 버전을 맞춘다.

```powershell
npm install --global npm@11.13.0
```

## 3. 일반 설치

### 백엔드

이 프로젝트의 사내망 설치 절차는 `venv` 또는 `virtualenv`를 사용하지 않는다. `python --version`이 정확히 `3.11.7`인지 확인한 뒤 서버의 시스템 Python에 패키지를 직접 설치한다. 다른 Python 버전의 `pip`가 실행되는 것을 막기 위해 모든 명령은 `python -m pip` 형식을 사용한다.

```powershell
cd D:\PO_MONITOR_MAIN
python -m pip install --upgrade pip
python -m pip install -r backend\requirements.txt
```

테스트까지 실행할 개발 PC는 다음 파일을 사용한다.

```powershell
python -m pip install -r backend\requirements-dev.txt
```

### 프론트엔드

`package-lock.json`에 고정된 버전을 그대로 설치하기 위해 `npm install`보다 `npm ci`를 사용한다.

```powershell
cd D:\PO_MONITOR_MAIN\frontend
npm ci
```

## 4. 사내 인증서가 있는 환경

가장 안전한 방법은 사내 Root CA 파일을 지정하는 것이다.

### pip

```powershell
python -m pip install `
  --cert C:\certs\company-root-ca.pem `
  -r backend\requirements.txt
```

사내 PyPI mirror가 있다면 다음처럼 사용한다.

```powershell
python -m pip install `
  --index-url https://pypi.company.local/simple `
  --cert C:\certs\company-root-ca.pem `
  -r backend\requirements.txt
```

### npm

```powershell
cd D:\PO_MONITOR_MAIN\frontend
npm config set cafile "C:\certs\company-root-ca.pem" --location=project
npm ci
```

사내 npm registry가 있다면:

```powershell
npm config set registry "https://npm.company.local/" --location=project
npm config set cafile "C:\certs\company-root-ca.pem" --location=project
npm ci
```

## 5. trusted-host 임시 설치

인증서 파일을 받을 수 없을 때만 사용한다. SSL 검증을 약화하므로 프로젝트 설치가 끝나면 원래 설정으로 되돌린다.

### pip trusted-host

```powershell
python -m pip install `
  --trusted-host pypi.org `
  --trusted-host files.pythonhosted.org `
  -r backend\requirements.txt
```

사내 mirror를 사용한다면 공개 호스트 대신 해당 mirror 호스트만 지정한다.

```powershell
python -m pip install `
  --index-url https://pypi.company.local/simple `
  --trusted-host pypi.company.local `
  -r backend\requirements.txt
```

### npm 임시 SSL 우회

npm에는 pip의 `trusted-host`와 같은 옵션이 없다. 필요한 경우 한 번의 설치 명령에만 SSL 우회를 적용한다.

```powershell
cd D:\PO_MONITOR_MAIN\frontend
npm --strict-ssl=false ci
```

전역 `npm config set strict-ssl false`는 다른 프로젝트까지 영향을 주므로 사용하지 않는다.

## 6. 완전 오프라인 설치 파일 준비

인터넷이 되는 Windows PC에서 프로젝트와 같은 Python·Node 버전을 설치한 후 준비한다.

### Python wheelhouse 만들기

```powershell
cd D:\PO_MONITOR_MAIN
New-Item -ItemType Directory -Force offline\python-wheels
python -m pip download `
  --dest offline\python-wheels `
  -r backend\requirements-dev.txt
```

사내망에서 설치:

```powershell
python -m pip install `
  --no-index `
  --find-links offline\python-wheels `
  -r backend\requirements-dev.txt
```

### npm cache 만들기

인터넷 PC:

```powershell
cd D:\PO_MONITOR_MAIN\frontend
npm ci --cache ..\offline\npm-cache
```

프로젝트의 `offline\npm-cache` 폴더도 함께 사내망으로 복사한다.

사내망:

```powershell
cd D:\PO_MONITOR_MAIN\frontend
npm ci --offline --cache ..\offline\npm-cache
```

사내망 npm이 일부 패키지 metadata를 추가로 요구한다면 인터넷 PC에서 `node_modules`를 포함해 압축한다. 이 경우에도 Windows/Node 버전과 CPU 아키텍처를 사내 PC와 동일하게 맞춘다.

## 7. 환경 설정과 DB

```powershell
cd D:\PO_MONITOR_MAIN
Copy-Item .env.example .env
notepad .env
```

`.env`에서 다음 범주를 설정한다.

- PostgreSQL `DATABASE_URL`
- `PO_SERVERS_JSON`
- SAP PO API 계정과 WSDL 경로
- RTIMS Oracle 접속정보
- JWT secret
- 허용된 CORS 주소

PostgreSQL migration은 번호 순서대로 한 번씩 적용한다.

```powershell
$psql = "C:\Program Files\PostgreSQL\17\bin\psql.exe"
& $psql -h localhost -p 5432 -U postgres -d po_monitor -f backend\migrations\001_initial.sql
& $psql -h localhost -p 5432 -U postgres -d po_monitor -f backend\migrations\002_dashboard_alert_llm.sql
& $psql -h localhost -p 5432 -U postgres -d po_monitor -f backend\migrations\003_workspaces.sql
& $psql -h localhost -p 5432 -U postgres -d po_monitor -f backend\migrations\004_monitoring_policy_and_iam.sql
& $psql -h localhost -p 5432 -U postgres -d po_monitor -f backend\migrations\005_required_feature_domains.sql
```

## 8. 실행과 확인

터미널 1:

```powershell
cd D:\PO_MONITOR_MAIN
python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000
```

터미널 2:

```powershell
cd D:\PO_MONITOR_MAIN\frontend
npm run dev
```

확인 주소:

```text
Frontend: http://localhost:3000
Backend health: http://localhost:8000/health
API documentation: http://localhost:8000/docs
```

운영 실행 전 확인:

```powershell
cd D:\PO_MONITOR_MAIN\frontend
npm run lint
npm test

cd D:\PO_MONITOR_MAIN
python -m pytest backend\tests
```
