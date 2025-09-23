
[Setup]
AppName=Telegram Multi-Account Message Sender
AppVersion=1.2.0
AppPublisher=VoxHash
AppPublisherURL=https://voxhash.dev
AppSupportURL=https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender/issues
AppUpdatesURL=https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender/releases
DefaultDirName={autopf}\TelegramMultiAccountSender
DefaultGroupName=Telegram Multi-Account Message Sender
AllowNoIcons=yes
LicenseFile=LICENSE
OutputDir=dist
OutputBaseFilename=TelegramMultiAccountSender-1.2.0-Windows
SetupIconFile=assets\icons\favicon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1

[Files]
Source: "dist\telegram-multi-account-sender\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "CHANGELOG.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Telegram Multi-Account Message Sender"; Filename: "{app}\telegram-multi-account-sender.exe"
Name: "{group}\{cm:UninstallProgram,Telegram Multi-Account Message Sender}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\Telegram Multi-Account Message Sender"; Filename: "{app}\telegram-multi-account-sender.exe"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\Telegram Multi-Account Message Sender"; Filename: "{app}\telegram-multi-account-sender.exe"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\telegram-multi-account-sender.exe"; Description: "{cm:LaunchProgram,Telegram Multi-Account Message Sender}"; Flags: nowait postinstall skipifsilent
