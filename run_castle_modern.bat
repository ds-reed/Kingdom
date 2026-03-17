@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" main.py --mode modern  --f demo_castle.json
    goto :done
)

where py >nul 2>nul
if %ERRORLEVEL%==0 (
    py main.py --mode modern  --f demo_castle.json
) else (
    python main.py --mode modern  --f demo_castle.json
)

:done
endlocal
