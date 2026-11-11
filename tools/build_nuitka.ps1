# Build ViberPrivacyBlur with Nuitka (native compile -> fewest antivirus false
# positives). Needs: PySide6-Essentials, pywin32, pillow, nuitka, pefile, and a
# C compiler. On Python 3.13+ Nuitka requires MSVC (Visual Studio Build Tools
# 2022 with the C++ workload); MinGW is only supported on Python <= 3.12.
#     powershell -ExecutionPolicy Bypass -File tools\build_nuitka.ps1
$ErrorActionPreference = "Stop"
$proj = Split-Path -Parent $PSScriptRoot

python "$proj\tools\make_icon.py"

python -m nuitka `
  --standalone `
  --msvc=latest `
  --assume-yes-for-downloads `
  --enable-plugin=pyside6 `
  --windows-console-mode=disable `
  --windows-icon-from-ico="$proj\assets\ViberPrivacyBlur.ico" `
  --company-name="Viber Privacy Blur" `
  --product-name="Viber Privacy Blur" `
  --file-description="Viber Privacy Blur - privacy overlay for Viber Desktop" `
  --file-version=1.1.0.0 `
  --product-version=1.1.0.0 `
  --copyright="Free utility" `
  --output-dir="$proj\build_nuitka" `
  --output-filename=ViberPrivacyBlur.exe `
  "$proj\main.py"

# Place the standalone folder at dist\ViberPrivacyBlur and fix the PE checksum.
if (Test-Path "$proj\dist\ViberPrivacyBlur") { Remove-Item -Recurse -Force "$proj\dist\ViberPrivacyBlur" }
New-Item -ItemType Directory -Force "$proj\dist" | Out-Null
Copy-Item -Recurse "$proj\build_nuitka\main.dist" "$proj\dist\ViberPrivacyBlur"
python "$proj\tools\fix_checksum.py" "$proj\dist\ViberPrivacyBlur\ViberPrivacyBlur.exe"

Write-Host "Built: $proj\dist\ViberPrivacyBlur\ (run ViberPrivacyBlur.exe)"
Write-Host "Next: compile the installer with  ISCC installer.iss"
