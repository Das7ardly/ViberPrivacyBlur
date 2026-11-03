; Inno Setup script for Viber Privacy Blur.
; Build:  ISCC.exe installer.iss   (produces installer\ViberPrivacyBlur-Setup-<ver>.exe)

#define AppName "Viber Privacy Blur"
#define AppVersion "1.0.0"
#define AppExe "ViberPrivacyBlur.exe"
#define Publisher "Viber Privacy Blur"
#define ProjDir SourcePath

[Setup]
AppId={{8F3C2B14-5D9A-4E77-9C21-A1B2C3D4E5F6}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#Publisher}
DefaultDirName={autopf}\ViberPrivacyBlur
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
DisableDirPage=auto
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir={#ProjDir}installer
OutputBaseFilename=ViberPrivacyBlur-Setup-{#AppVersion}
SetupIconFile={#ProjDir}assets\ViberPrivacyBlur.ico
UninstallDisplayIcon={app}\{#AppExe}
UninstallDisplayName={#AppName}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Tasks]
Name: "startup"; Description: "Start {#AppName} automatically when Windows starts"; GroupDescription: "Startup:"
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Shortcuts:"

[Files]
; onedir build: ship the whole program folder (exe + _internal\ runtime).
Source: "{#ProjDir}dist\ViberPrivacyBlur\*"; DestDir: "{app}"; \
  Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#ProjDir}README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; \
  ValueType: string; ValueName: "ViberPrivacyBlur"; ValueData: """{app}\{#AppExe}"""; \
  Flags: uninsdeletevalue; Tasks: startup

[Run]
Filename: "{app}\{#AppExe}"; Description: "Launch {#AppName} now"; \
  Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{sys}\taskkill.exe"; Parameters: "/IM {#AppExe} /F"; \
  Flags: runhidden; RunOnceId: "killapp"

[Code]
procedure KillRunning;
var
  RC: Integer;
begin
  Exec(ExpandConstant('{sys}\taskkill.exe'), '/IM ViberPrivacyBlur.exe /F', '',
       SW_HIDE, ewWaitUntilTerminated, RC);
end;

function InitializeSetup(): Boolean;
begin
  KillRunning();   { close any running copy before (re)installing }
  Result := True;
end;
