; Inno Setup script for the ToDoList installer. build.py compiles it after PyInstaller:
;   ISCC.exe /DAppVersion=0.1.0 packaging\ToDoList.iss
; Per-user install (no admin rights). Uninstall keeps the user's data in %APPDATA%\ToDoList.

#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif

[Setup]
AppId={{6F2C8B1E-4D3A-4E7B-9C51-2A8D0F3B7E64}
AppName=ToDoList
AppVersion={#AppVersion}
AppPublisher=SanghyeonYun
DefaultDirName={localappdata}\Programs\ToDoList
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\dist
OutputBaseFilename=ToDoList-Setup-{#AppVersion}
SetupIconFile=..\build\app.ico
UninstallDisplayIcon={app}\ToDoList.exe
UninstallDisplayName=ToDoList
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
Source: "..\dist\ToDoList\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\ToDoList"; Filename: "{app}\ToDoList.exe"
Name: "{autodesktop}\ToDoList"; Filename: "{app}\ToDoList.exe"; Tasks: desktopicon

[Registry]
; Same entry the app's Settings toggle writes (todolist/autostart.py).
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "ToDoList"; ValueData: """{app}\ToDoList.exe"""; Flags: uninsdeletevalue; Tasks: autostart

[Run]
Filename: "{app}\ToDoList.exe"; Description: "{cm:LaunchProgram,ToDoList}"; Flags: nowait postinstall skipifsilent
