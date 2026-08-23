@echo off
setlocal
cd /d "%~dp0"
python scripts\setup_rtims_databases.py --target all --apply --env-file .env
set "EXIT_CODE=%ERRORLEVEL%"
if not "%EXIT_CODE%"=="0" echo RTIMS schema setup failed. Review the safe error above.
if "%EXIT_CODE%"=="0" echo RTIMS schema setup completed.
pause
exit /b %EXIT_CODE%
