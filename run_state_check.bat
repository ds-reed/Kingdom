@echo off
setlocal
cd /d "%~dp0"

if "%~1"=="" (
    set "ARGS=data\initial_state.json data\working_state.json data\demo_initial_state.json"
) else (
    set "ARGS=%*"
)

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" scripts\check_world_json.py %ARGS%
    goto :done
)

where py >nul 2>nul
if %ERRORLEVEL%==0 (
    py scripts\check_world_json.py %ARGS%
) else (
    python scripts\check_world_json.py %ARGS%
)

:done
echo.
pause
endlocal
