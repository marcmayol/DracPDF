; Instalador de DracPDF (Inno Setup).
; Compilar con: uv run python scripts/construir_instalador.py
; Instalación por usuario (sin privilegios de administrador).

#define MyAppName "DracPDF"
; La versión la inyecta publicar_release.py por ISCC /DMyAppVersion=<__version__>
; (fuente única: src/lectorpdf/__init__.py). Este valor por defecto solo sirve
; para compilar a mano sin pasar el define.
#ifndef MyAppVersion
  #define MyAppVersion "0.0.0-dev"
#endif
#define MyAppPublisher "Marc Mayol"
#define MyAppContact "marcmayolorell@gmail.com"
#define MyAppExeName "DracPDF.exe"
#define MyAppProgId "DracPDF.pdf"

[Setup]
AppId={{7B2F3C4A-9D51-4E88-A2C6-DRACPDF00001}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL=mailto:{#MyAppContact}
AppSupportURL=mailto:{#MyAppContact}
AppContact={#MyAppContact}
; Instalación por usuario: sin UAC, en %LOCALAPPDATA%\Programs.
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
SourceDir={#SourcePath}\..
OutputDir=dist\installer
OutputBaseFilename=DracPDF-{#MyAppVersion}-setup
SetupIconFile=build\icons\ladon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
ArchitecturesAllowed=x64compatible

[Languages]
Name: "es"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "en"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
; Asociación de PDF: OPCIONAL y desmarcada. Solo registra DracPDF como opción
; para abrir .pdf; NO fuerza el predeterminado (lo eliges tú en "Abrir con").
Name: "pdfassoc"; Description: "Registrar DracPDF para abrir archivos PDF (podrás elegirlo en «Abrir con»)"; GroupDescription: "Asociaciones:"; Flags: unchecked

[Files]
Source: "dist\DracPDF.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{userdesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
; ProgID propio de DracPDF (abre el PDF pasándolo como argumento).
Root: HKCU; Subkey: "Software\Classes\{#MyAppProgId}"; ValueType: string; ValueName: ""; ValueData: "Documento PDF (DracPDF)"; Flags: uninsdeletekey; Tasks: pdfassoc
Root: HKCU; Subkey: "Software\Classes\{#MyAppProgId}\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MyAppExeName},0"; Tasks: pdfassoc
Root: HKCU; Subkey: "Software\Classes\{#MyAppProgId}\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Tasks: pdfassoc
; Añadir DracPDF a la lista "Abrir con" de .pdf (sin tocar el predeterminado).
Root: HKCU; Subkey: "Software\Classes\.pdf\OpenWithProgids"; ValueType: string; ValueName: "{#MyAppProgId}"; ValueData: ""; Flags: uninsdeletevalue; Tasks: pdfassoc
; Registrar la app y sus capacidades (para "Aplicaciones predeterminadas" de Windows).
; La clave raíz se marca para borrado completo (se instala primero, se elimina la
; última al desinstalar, sin dejar claves vacías).
Root: HKCU; Subkey: "Software\{#MyAppName}"; Flags: uninsdeletekey; Tasks: pdfassoc
Root: HKCU; Subkey: "Software\{#MyAppName}\Capabilities"; ValueType: string; ValueName: "ApplicationName"; ValueData: "{#MyAppName}"; Tasks: pdfassoc
Root: HKCU; Subkey: "Software\{#MyAppName}\Capabilities"; ValueType: string; ValueName: "ApplicationDescription"; ValueData: "Visor y firmador de PDF"; Tasks: pdfassoc
Root: HKCU; Subkey: "Software\{#MyAppName}\Capabilities\FileAssociations"; ValueType: string; ValueName: ".pdf"; ValueData: "{#MyAppProgId}"; Tasks: pdfassoc
Root: HKCU; Subkey: "Software\RegisteredApplications"; ValueType: string; ValueName: "{#MyAppName}"; ValueData: "Software\{#MyAppName}\Capabilities"; Flags: uninsdeletevalue; Tasks: pdfassoc

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent
