#define MyAppName "PhotoDock"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "WJay7"
#define MyAppExeName "PhotoDock.exe"

[Setup]
AppId={{9C2B4A14-3A4F-4FCB-9D8E-4D1EAB5E7A21}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
SetupIconFile=..\assets\photodock.ico
DefaultDirName={autopf}\PhotoDock
DefaultGroupName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
OutputDir=..\dist
OutputBaseFilename=PhotoDock-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
; 使用 Inno Setup Runner 自带语言文件，避免精简安装包缺少中文语言包导致编译失败。
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加快捷方式："

[Files]
Source: "..\dist\PhotoDock.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\PhotoDock"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\PhotoDock"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "启动 PhotoDock"; Flags: nowait postinstall skipifsilent
