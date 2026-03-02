@echo off
setlocal
cd /d "%~dp0"

if "%~1"=="" (
    set "ARGS=data\initial_state.json"
) else (
    set "ARGS=%*"
)

set "PYTHON_CMD="
if exist ".venv\Scripts\python.exe" (
    set "PYTHON_CMD=.venv\Scripts\python.exe"
    goto :run_checks
)

where py >nul 2>nul
if %ERRORLEVEL%==0 (
    set "PYTHON_CMD=py"
) else (
    set "PYTHON_CMD=python"
)

:run_checks
set "STATUS=0"

echo Running world JSON checks...
%PYTHON_CMD% scripts\check_world_json.py %ARGS%
if %ERRORLEVEL% neq 0 set "STATUS=1"

echo.
echo Running save/load roundtrip validation...
%PYTHON_CMD% scripts\validate_save_load_roundtrip.py
if %ERRORLEVEL% neq 0 set "STATUS=1"

if %STATUS% neq 0 (
    echo.
    echo One or more checks failed.
) else (
    echo.
    echo All checks passed.
)

:done
echo.
pause
endlocal
