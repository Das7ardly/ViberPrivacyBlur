# Build ViberPrivacyBlur (onedir) with PyInstaller, then fix the PE checksum.
# onedir (not onefile) + real version info + a valid checksum => fewer antivirus
# false positives. Run from a Python env with:
#   PySide6-Essentials, pywin32, pillow, pyinstaller, pefile
#     powershell -ExecutionPolicy Bypass -File tools\build.ps1
$ErrorActionPreference = "Stop"
$proj = Split-Path -Parent $PSScriptRoot

python "$proj\tools\make_icon.py"

python -m PyInstaller --noconfirm --clean --windowed --onedir `
  --name ViberPrivacyBlur `
  --icon "$proj\assets\ViberPrivacyBlur.ico" `
  --version-file "$proj\tools\version_info.txt" `
  --distpath "$proj\dist" `
  --exclude-module PySide6.QtNetwork --exclude-module PySide6.QtQml --exclude-module PySide6.QtQuick `
  --exclude-module PySide6.QtQuickWidgets --exclude-module PySide6.QtPdf --exclude-module PySide6.QtPdfWidgets `
  --exclude-module PySide6.QtSql --exclude-module PySide6.QtMultimedia --exclude-module PySide6.QtMultimediaWidgets `
  --exclude-module PySide6.QtWebEngineCore --exclude-module PySide6.QtWebEngineWidgets --exclude-module PySide6.QtWebChannel `
  --exclude-module PySide6.QtWebSockets --exclude-module PySide6.QtCharts --exclude-module PySide6.QtOpenGL `
  --exclude-module PySide6.QtOpenGLWidgets --exclude-module PySide6.QtTest --exclude-module PySide6.QtDesigner `
  --exclude-module tkinter --exclude-module numpy --exclude-module scipy `
  "$proj\main.py"

python "$proj\tools\fix_checksum.py" "$proj\dist\ViberPrivacyBlur\ViberPrivacyBlur.exe"

Write-Host "Built: $proj\dist\ViberPrivacyBlur\ (run ViberPrivacyBlur.exe)"
Write-Host "Next: compile the installer with  ISCC installer.iss"
