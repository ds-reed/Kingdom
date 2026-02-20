@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" main.py
    goto :done
)

where py >nul 2>nul
if %ERRORLEVEL%==0 (
    py main.py
) else (
    python main.py
)

:done
endlocal
