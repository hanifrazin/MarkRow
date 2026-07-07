@echo off
setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%..\.."
cd /d "%PROJECT_ROOT%"
set "PROJECT_ROOT=%CD%"

set "VENV_DIR=%PROJECT_ROOT%\.venv"
set "REQ_FILE=%PROJECT_ROOT%\requirements.txt"
set "MAIN_PY=%PROJECT_ROOT%\src\main.py"
set "BINARY=%PROJECT_ROOT%\.build_cache\dist\mamow.exe"

if not exist "%VENV_DIR%" (
    echo Initializing virtual environment...
    python -m venv "%VENV_DIR%"
    "%VENV_DIR%\Scripts\pip.exe" install --quiet --upgrade pip
    "%VENV_DIR%\Scripts\pip.exe" install --quiet -r "%REQ_FILE%"
)

if not exist "%BINARY%" (
    echo Building binary with PyInstaller ^(this may take 1-2 minutes on first run^)...
    if not exist "%PROJECT_ROOT%\.build_cache" mkdir "%PROJECT_ROOT%\.build_cache"
    "%VENV_DIR%\Scripts\pyinstaller.exe" --noconfirm --onefile --name mamow --distpath "%PROJECT_ROOT%\.build_cache\dist" --workpath "%PROJECT_ROOT%\.build_cache\build" --specpath "%PROJECT_ROOT%\.build_cache" "%MAIN_PY%" >nul 2>&1
)

if exist "%BINARY%" (
    "%BINARY%" %*
) else (
    echo Warning: Binary not found. Falling back to Python execution.
    "%VENV_DIR%\Scripts\python.exe" "%MAIN_PY%" %*
)
