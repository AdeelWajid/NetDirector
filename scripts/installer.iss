#ifndef MyAppVersion
  #define MyAppVersion "0.0.1"
#endif
#ifndef MyAppArch
  #define MyAppArch "x64"
#endif

[Setup]
AppId={{D37E88A1-88BA-4E4E-A528-9891F47A4A9C}
AppName=NetDirector
AppVersion={#MyAppVersion}
AppPublisher=NetDirector
AppPublisherURL=https://github.com/AdeelWajid/NetDirector
AppSupportURL=https://github.com/AdeelWajid/NetDirector/issues
AppUpdatesURL=https://github.com/AdeelWajid/NetDirector/releases
DefaultDirName={autopf}\NetDirector
DefaultGroupName=NetDirector
AllowNoIcons=yes
LicenseFile=..\LICENSE
OutputDir=..\release
OutputBaseFilename=NetDirector-{#MyAppVersion}-windows-{#MyAppArch}-Setup
SetupIconFile=..\assets\netdirector.ico
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
#if MyAppArch == "x64"
ArchitecturesInstallIn64BitMode=x64compatible
#endif

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Main NetDirector application bundle
Source: "..\dist\{#MyAppArch}\NetDirector\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; ForceBindIP integration files installed to LocalAppData
Source: "..\dist\{#MyAppArch}\NetDirector\ForceBindIP\*"; DestDir: "{localappdata}\ForceBindIP"; Flags: ignoreversion uninsneveruninstall

[Icons]
Name: "{group}\NetDirector"; Filename: "{app}\NetDirector.exe"
Name: "{group}\{cm:UninstallProgram,NetDirector}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\NetDirector"; Filename: "{app}\NetDirector.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\NetDirector.exe"; Description: "{cm:LaunchProgram,NetDirector}"; Flags: nowait postinstall skipifsilent
