; AEGIS-DocIntel Windows x64 Inno Setup Installer Script
; Version: 1.0.0-beta.1
; Target Platform: Windows 10/11 64-bit

#define MyAppName "AEGIS-DocIntel"
#define MyAppVersion "1.0.0-beta.1"
#define MyAppPublisher "Google DeepMind / AEGIS-DocIntel"
#define MyAppURL "https://github.com/SahilKhutey/AEGIS-DocIntel"
#define MyAppExeName "AEGIS-DocIntel.bat"

[Setup]
AppId={{5E97D45A-8E5A-4B69-952F-77D95B94BE7C}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={userpf}\{#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=..\..\..\client-template\licenses\LICENSE
OutputDir=.
OutputBaseFilename=AEGIS-DocIntel-Setup
SetupIconFile=..\..\..\client-template\assets\icons\app-icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\assets\icons\app-icon.ico

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\..\..\client-template\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{userprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\icons\app-icon.ico"
Name: "{userdesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; IconFilename: "{app}\assets\icons\app-icon.ico"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: shellexec postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\backups"
