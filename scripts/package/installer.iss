#define AppVersion "0.2.0"
#define AppId "{{C6B25744-98A8-4B23-B4CF-3E45CA29944E}"
#define RegistryId "{C6B25744-98A8-4B23-B4CF-3E45CA29944E}"
#ifndef PayloadDir
  #error PayloadDir is required
#endif
#ifndef OutputDir
  #error OutputDir is required
#endif
[Setup]
AppId={#AppId}
AppName=Local Document Search v2
AppVersion={#AppVersion}
AppPublisher=Local Document Search
InfoBeforeFile={#SourcePath}\TERMS-IT.txt
DefaultDirName={localappdata}\Programs\LocalDocumentSearchV2
DefaultGroupName=Local Document Search v2
OutputDir={#OutputDir}
OutputBaseFilename=LocalDocumentSearch-0.2.0-windows-x64-setup
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UsePreviousAppDir=no
DisableDirPage=yes
DisableProgramGroupPage=yes
CloseApplications=no
RestartApplications=no
UninstallDisplayIcon={app}\LocalDocumentSearch.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupIconFile={#SourcePath}\..\..\frontend\src\local_document_search_desktop\assets\luma.ico
SetupLogging=yes

[Languages]
Name: "it"; MessagesFile: "compiler:Languages\Italian.isl"
Name: "en"; MessagesFile: "compiler:Default.isl"; InfoBeforeFile: "{#SourcePath}\TERMS-EN.txt"

[CustomMessages]
it.CloseForInstall=Chiudere Local Document Search prima di installare o aggiornare.
en.CloseForInstall=Close Local Document Search before installing or updating.
it.Downgrade=È già installata una versione più recente. Il downgrade è bloccato.
en.Downgrade=A newer version is already installed. Downgrade is blocked.
it.CloseForUninstall=Chiudere Local Document Search prima della disinstallazione.
en.CloseForUninstall=Close Local Document Search before uninstalling.
it.DeleteData=Eliminare indici e preferenze di Local Document Search v2? L'operazione non può essere annullata.
en.DeleteData=Delete Local Document Search v2 indexes and preferences? This cannot be undone.
it.CleanupFailed=La pulizia dei dati è fallita. Chiudere l'applicazione e riprovare.
en.CleanupFailed=Data cleanup failed. Close the application and retry.
it.UpgradeFailed=Impossibile eliminare i vecchi file applicativi. Riprovare l'installer.
en.UpgradeFailed=Old application files could not be removed. Retry the installer.

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; Flags: unchecked

[Files]
Source: "{#PayloadDir}\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "{#SourcePath}\uninstall-data.ps1"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourcePath}\prune-upgrade.ps1"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\Local Document Search v2"; Filename: "{app}\LocalDocumentSearch.exe"
Name: "{autodesktop}\Local Document Search v2"; Filename: "{app}\LocalDocumentSearch.exe"; Tasks: desktopicon

[Code]
const RunningMutex = 'Local\LocalDocumentSearchV2Running';
var DeleteData: Boolean;
    PreviousManifest: String;

function VersionPart(var S: String): Integer;
var P: Integer;
begin
  P := Pos('.', S);
  if P = 0 then begin Result := StrToIntDef(S, 0); S := ''; end
  else begin Result := StrToIntDef(Copy(S, 1, P - 1), 0); Delete(S, 1, P); end;
end;

function OlderVersion(Installed, Candidate: String): Boolean;
var A, B, I: Integer;
begin
  Result := False;
  for I := 1 to 3 do begin
    A := VersionPart(Installed); B := VersionPart(Candidate);
    if A <> B then begin Result := A > B; Exit; end;
  end;
end;

function InitializeSetup(): Boolean;
var Installed: String;
begin
  Result := False;
  if CheckForMutexes(RunningMutex) then begin
    if not WizardSilent then MsgBox(ExpandConstant('{cm:CloseForInstall}'), mbError, MB_OK);
    Exit;
  end;
  if RegQueryStringValue(HKCU, 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{#RegistryId}_is1', 'DisplayVersion', Installed) and
     OlderVersion(Installed, '{#AppVersion}') then begin
    if not WizardSilent then MsgBox(ExpandConstant('{cm:Downgrade}'), mbError, MB_OK);
    Exit;
  end;
  Result := True;
end;

function InitializeUninstall(): Boolean;
begin
  Result := not CheckForMutexes(RunningMutex);
  if not Result and not UninstallSilent then MsgBox(ExpandConstant('{cm:CloseForUninstall}'), mbError, MB_OK);
  DeleteData := False;
  if Result and not UninstallSilent then
    DeleteData := MsgBox(ExpandConstant('{cm:DeleteData}'), mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var ExitCode: Integer; Root, Script: String;
begin
  if CurStep = ssInstall then begin
    Root := ExpandConstant('{app}');
    PreviousManifest := ExpandConstant('{tmp}\previous-build-manifest.json');
    if FileExists(Root + '\BUILD-MANIFEST.json') then
      CopyFile(Root + '\BUILD-MANIFEST.json', PreviousManifest, False);
  end;
  if (CurStep = ssPostInstall) and FileExists(PreviousManifest) then begin
    Script := ExpandConstant('{app}\prune-upgrade.ps1');
    if not Exec(ExpandConstant('{sys}\WindowsPowerShell\v1.0\powershell.exe'),
      '-NoProfile -NonInteractive -ExecutionPolicy Bypass -File "' + Script +
      '" -InstallRoot "' + ExpandConstant('{app}') + '" -PreviousManifest "' + PreviousManifest + '"',
      '', SW_HIDE, ewWaitUntilTerminated, ExitCode) or (ExitCode <> 0) then
      RaiseException(ExpandConstant('{cm:UpgradeFailed}'));
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var ExitCode: Integer; Script: String;
begin
  if (CurUninstallStep = usUninstall) and DeleteData then begin
    Script := ExpandConstant('{app}\uninstall-data.ps1');
    if not Exec(ExpandConstant('{sys}\WindowsPowerShell\v1.0\powershell.exe'),
      '-NoProfile -NonInteractive -ExecutionPolicy Bypass -File "' + Script + '"',
      '', SW_HIDE, ewWaitUntilTerminated, ExitCode) or (ExitCode <> 0) then
      RaiseException(ExpandConstant('{cm:CleanupFailed}'));
  end;
end;
