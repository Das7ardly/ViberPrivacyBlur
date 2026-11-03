<#
Code-sign Viber Privacy Blur, then rebuild & sign the installer.

This is ready to use the moment you have a code-signing certificate. It signs the
app exe first, recompiles the installer so it bundles the SIGNED exe, then signs
the installer itself (SHA-256 + RFC-3161 timestamp so signatures stay valid after
the cert expires).

Requirements:
  - signtool.exe (Windows 10/11 SDK; or the "Windows SDK" component in Visual
    Studio Build Tools). The script auto-locates it.
  - The app already built:  tools\build_nuitka.ps1
  - Inno Setup (ISCC) for the installer step.

Usage with a .pfx certificate file:
  powershell -ExecutionPolicy Bypass -File tools\sign.ps1 -PfxPath C:\path\to\cert.pfx -PfxPassword "yourpassword"

Usage with a certificate already imported into the Windows cert store:
  powershell -ExecutionPolicy Bypass -File tools\sign.ps1 -Thumbprint 1A2B3C...

Options:
  -TimestampUrl <url>   RFC-3161 timestamp server (default: DigiCert)
  -SkipInstaller        Sign only the app exe
#>
param(
  [string]$PfxPath,
  [string]$PfxPassword,
  [string]$Thumbprint,
  [string]$TimestampUrl = "http://timestamp.digicert.com",
  [switch]$SkipInstaller
)
$ErrorActionPreference = "Stop"
$proj = Split-Path -Parent $PSScriptRoot

function Find-SignTool {
  $roots = @("${env:ProgramFiles(x86)}\Windows Kits\10\bin", "${env:ProgramFiles}\Windows Kits\10\bin")
  $hits = @()
  foreach ($root in $roots) {
    if (Test-Path $root) {
      $hits += Get-ChildItem -Path $root -Recurse -Filter signtool.exe -ErrorAction SilentlyContinue |
               Where-Object { $_.FullName -match "\\x64\\" }
    }
  }
  if ($hits.Count -eq 0) {
    throw "signtool.exe not found. Install the Windows 10/11 SDK (standalone, or the 'Windows SDK' component in Visual Studio Build Tools 2022)."
  }
  ($hits | Sort-Object FullName -Descending | Select-Object -First 1).FullName
}

$signtool = Find-SignTool
Write-Host "Using signtool: $signtool"

function Sign-File([string]$file) {
  if (-not (Test-Path $file)) { throw "File to sign not found: $file" }
  $common = @("sign", "/fd", "SHA256", "/tr", $TimestampUrl, "/td", "SHA256", "/v")
  if ($Thumbprint) {
    $sargs = $common + @("/sha1", $Thumbprint, $file)
  } elseif ($PfxPath) {
    $sargs = $common + @("/f", $PfxPath)
    if ($PfxPassword) { $sargs += @("/p", $PfxPassword) }
    $sargs += $file
  } else {
    throw "Provide either -PfxPath (with -PfxPassword) or -Thumbprint."
  }
  Write-Host "Signing: $file"
  & $signtool @sargs
  if ($LASTEXITCODE -ne 0) { throw "signtool failed on $file" }
  & $signtool verify /pa /v $file
  if ($LASTEXITCODE -ne 0) { throw "signature verification failed on $file" }
}

# 1) Sign the application exe.
$appExe = Join-Path $proj "dist\ViberPrivacyBlur\ViberPrivacyBlur.exe"
if (-not (Test-Path $appExe)) { throw "App exe not found: $appExe  (build first: tools\build_nuitka.ps1)" }
Sign-File $appExe

# 2) Rebuild the installer (so it bundles the signed exe), then sign the installer.
if (-not $SkipInstaller) {
  $iscc = "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
  if (-not (Test-Path $iscc)) { $iscc = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe" }
  if (Test-Path $iscc) {
    Write-Host "Rebuilding installer with the signed exe..."
    & $iscc "$proj\installer.iss"
    if ($LASTEXITCODE -ne 0) { throw "ISCC failed" }
    Sign-File (Join-Path $proj "installer\ViberPrivacyBlur-Setup-1.0.0.exe")
  } else {
    Write-Warning "ISCC not found - installer not rebuilt. The app exe is signed; re-run with ISCC available to sign the installer."
  }
}

Write-Host ""
Write-Host "Done - app exe and installer are signed and verified." -ForegroundColor Green
