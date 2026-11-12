; Instalador do Pestinha Pro para Windows (Inno Setup 6). Instala só para o usuário atual, sem pedir administrador.
; Gera um único arquivo instalador .exe com Python, PySide6 e todas as dependências embutidas.
; Sai em instalador\saida\. A memória fica em %LOCALAPPDATA%\Pestinha e não é apagada ao desinstalar.

#define Versao "2.0.0"

[Setup]
AppId={{7C7C1F0E-5B0A-4B57-9A63-6E2E5A3F8D10}
AppName=Pestinha Pro
AppVersion={#Versao}
AppPublisher=mille-okws & Moa
AppPublisherURL=https://github.com/mille-okws/pestinha
AppSupportURL=https://github.com/mille-okws/pestinha
AppUpdatesURL=https://github.com/mille-okws/pestinha
DefaultDirName={localappdata}\Programs\Pestinha Pro
DefaultGroupName=Pestinha Pro
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=saida
OutputBaseFilename=Pestinha-Pro-{#Versao}-Instalador
UninstallDisplayIcon={app}\Pestinha.exe
LicenseFile=..\LICENSE
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "atalho"; Description: "Criar atalho na Área de Trabalho"; Flags: unchecked
Name: "iniciar_com_windows"; Description: "Iniciar o Pestinha Pro ao ligar o computador"; Flags: unchecked

[Files]
Source: "..\dist\Pestinha.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs
Source: "..\pets\*"; DestDir: "{app}\pets"; Flags: ignoreversion recursesubdirs
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\PRIVACIDADE.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Pestinha Pro"; Filename: "{app}\Pestinha.exe"
Name: "{group}\Configurar o Pestinha Pro"; Filename: "{app}\Pestinha.exe"; Parameters: "--configurar"
Name: "{userdesktop}\Pestinha Pro"; Filename: "{app}\Pestinha.exe"; Tasks: atalho

[Registry]
; Opção opcional de iniciar com o Windows escolhida pelo instalador
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueName: "Pestinha Pro"; ValueType: string; ValueData: """{app}\Pestinha.exe"""; Flags: uninsdeletevalue; Tasks: iniciar_com_windows

[Run]
Filename: "{app}\Pestinha.exe"; Description: "Abrir o Pestinha Pro agora"; Flags: nowait postinstall skipifsilent
