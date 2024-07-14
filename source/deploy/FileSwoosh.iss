[Setup]
; The name of the application
AppName={#app_name} {#version}
; The version
AppVersion={#version}
; The publisher name
AppPublisher=Henri Wahl
; The application website
AppPublisherURL=https://github.com/henriwahl-iu/FileSwoosh
; The directory for the application; {commonpf64} refers to the Program Files x64 directory
DefaultDirName={commonpf64}\{#app_name}
; The application's default group name in the Start Menu
DefaultGroupName={#app_name}
; The output base filename of the setup executable
OutputBaseFilename={#output_base_filename}
; Compression settings
Compression=lzma
SolidCompression=yes
; Icon settings
SetupIconFile=..\resources\images\logo.ico
UninstallDisplayIcon=..\resources\images\logo.ico
; Don't ask for program group
DisableProgramGroupPage=yes

[Files]
; Specifies which files to include in the installation
; Adjust the source directory as needed to point to your built application files
Source: "..\dist\{#app_name}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Create a program group and an icon in the Start Menu
Name: "{group}\{#app_name}"; Filename: "{app}\{#app_name}.exe"
; Create a desktop icon for all users
Name: "{commondesktop}\{#app_name}"; Filename: "{app}\{#app_name}.exe";

[Run]
Filename: powershell.exe; \
  Parameters: "New-NetFirewallRule -DisplayName FileSwoosh -Program ""'{app}\{#app_name}.exe'"" -Action Allow -Direction Inbound"; \
  Description: "Open Firewall inbound for {#app_name}"; \
  Flags: nowait runhidden;
Filename: powershell.exe; \
  Parameters: "New-NetFirewallRule -DisplayName FileSwoosh -Program ""'{app}\{#app_name}.exe'"" -Action Allow -Direction Outbound"; \
  Description: "Open Firewall outbound for {#app_name}"; \
  Flags: nowait runhidden;

[UninstallRun]
Filename: powershell.exe; \
  Parameters: "Remove-NetFirewallRule -DisplayName FileSwoosh"; \
  Flags: nowait runhidden; \
  RunOnceId: RemoveFirewallRule