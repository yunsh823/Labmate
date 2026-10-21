; Inno Setup script for the Labmate installer. build.py compiles it after PyInstaller:
;   ISCC.exe /DAppVersion=0.1.0 packaging\Labmate.iss
; Per-user install (no admin rights). Uninstall keeps the user's data in %APPDATA%\Labmate.

#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif

[Setup]
AppId={{6F2C8B1E-4D3A-4E7B-9C51-2A8D0F3B7E64}
AppName=Labmate
AppVersion={#AppVersion}
AppPublisher=SanghyeonYun
DefaultDirName={localappdata}\Programs\Labmate
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\dist
OutputBaseFilename=Labmate-Setup-{#AppVersion}
SetupIconFile=..\build\app.ico
UninstallDisplayIcon={app}\Labmate.exe
UninstallDisplayName=Labmate
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
; Close a running copy (it lives in the tray) before replacing its files.
CloseApplications=force

[Languages]
Name: "korean"; MessagesFile: "compiler:Languages\Korean.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[CustomMessages]
korean.AutoStart=Windows 시작 시 자동 실행
english.AutoStart=Start with Windows

[Tasks]
Name: "autostart"; Description: "{cm:AutoStart}"
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\Labmate\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\Labmate"; Filename: "{app}\Labmate.exe"
Name: "{autodesktop}\Labmate"; Filename: "{app}\Labmate.exe"; Tasks: desktopicon

[Registry]
; Same entry the app's Settings toggle writes (labmate/autostart.py).
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "Labmate"; ValueData: """{app}\Labmate.exe"""; Flags: uninsdeletevalue; Tasks: autostart

[Run]
Filename: "{app}\Labmate.exe"; Description: "{cm:LaunchProgram,Labmate}"; Flags: nowait postinstall skipifsilent

[Code]
// The app hides to the tray instead of quitting on a close request, so Windows'
// "close running apps" can't stop it. End it outright before files are replaced or
// removed; every change is already saved to the database, so nothing is lost.
procedure EndRunningApp();
var
  ResultCode: Integer;
begin
  Exec(ExpandConstant('{sys}\taskkill.exe'), '/F /IM Labmate.exe', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  Sleep(500);
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  EndRunningApp();
  Result := '';
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usUninstall then
    EndRunningApp();
end;
