@echo off
cd /d "%~dp0"
python -c "import sys; assert sys.version_info[:3] == (3, 11, 7); import uvicorn" >nul 2>&1
if errorlevel 1 (
  echo Python 3.11.7 or backend packages not found. Follow README.md first.
  exit /b 1
)
python -m uvicorn app.main:app --app-dir backend --reload --port 8000
