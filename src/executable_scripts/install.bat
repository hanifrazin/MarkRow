@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%..\.."
cd /d "%PROJECT_ROOT%"
set "PROJECT_ROOT=%CD%"
set "SCRIPTS_DIR=%PROJECT_ROOT%\src\executable_scripts"

echo Installing MaMoW to User PATH...

for /f "tokens=2,*" %%A in ('reg query HKCU\Environment /v PATH 2^>nul') do (
    set "USER_PATH=%%B"
)

if not defined USER_PATH (
    set "NEW_PATH=%SCRIPTS_DIR%"
    goto :SetPath
)

echo %USER_PATH% | findstr /i /c:"%SCRIPTS_DIR%" >nul
if %errorlevel% equ 0 (
    echo Path already configured.
    goto :End
)

set "NEW_PATH=%USER_PATH%;%SCRIPTS_DIR%"

:SetPath
setx PATH "%NEW_PATH%"
echo Appended %SCRIPTS_DIR% to user PATH.

:End
echo Installation complete! You can now use the 'mamow' command globally.
pause
