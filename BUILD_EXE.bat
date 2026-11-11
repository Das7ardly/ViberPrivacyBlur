@echo off
rem Builds dist\ViberPrivacyBlur\ViberPrivacyBlur.exe. Needs Python 3.10+ installed.
setlocal
cd /d "%~dp0"
set PY=python
where py >nul 2>nul && set PY=py -3
%PY% --version >nul 2>nul
if errorlevel 1 (
  echo Python 3 was not found. Install it from https://www.python.org/downloads/ and run this again.
  goto :fail
)
if not exist ".venv-build\Scripts\python.exe" %PY% -m venv .venv-build
if not exist ".venv-build\Scripts\python.exe" goto :fail
call ".venv-build\Scripts\activate.bat"
python -m pip install --quiet --upgrade pip
python -m pip install --quiet PySide6-Essentials pywin32 pillow pyinstaller pefile
if errorlevel 1 goto :fail
powershell -NoProfile -ExecutionPolicy Bypass -File "tools\build.ps1"
if not exist "dist\ViberPrivacyBlur\ViberPrivacyBlur.exe" goto :fail
echo.
echo Built: %cd%\dist\ViberPrivacyBlur\ViberPrivacyBlur.exe
start "" explorer "dist\ViberPrivacyBlur"
pause
exit /b 0
:fail
echo.
echo Build failed. Copy the text above and send it to Claude.
pause
exit /b 1
