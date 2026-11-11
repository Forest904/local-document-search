#define AppVersion "0.2.1"
#define AppId "{{C6B25744-98A8-4B23-B4CF-3E45CA29944E}"
#define RegistryId "{C6B25744-98A8-4B23-B4CF-3E45CA29944E}"
#ifndef PayloadDir
  #error PayloadDir is required
#endif
#ifndef OutputDir
  #error OutputDir is required
#endif
#ifndef RequiredBytes
  #define RequiredBytes "0"
#endif
[Setup]
AppId={#AppId}
AppName=Local Document Search
AppVersion={#AppVersion}
AppPublisher=Local Document Search
InfoBeforeFile={#SourcePath}\TERMS-IT.txt
DefaultDirName={localappdata}\Programs\LocalDocumentSearch
DefaultGroupName=Local Document Search
OutputDir={#OutputDir}
OutputBaseFilename=LocalDocumentSearch-0.2.1-windows-x64-setup
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UsePreviousAppDir=yes
DisableDirPage=no
AppendDefaultDirName=yes
AllowUNCPath=no
AllowNetworkDrive=no
AllowRootDirectory=no
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
it.CloseForInstall=Chiudere Local Document Search, poi scegliere Riprova.
en.CloseForInstall=Close Local Document Search, then choose Retry.
it.InvalidDestination=La cartella deve essere nuova o vuota, su un disco locale fisso, scrivibile e senza collegamenti o junction. Scegliere un'altra cartella.
en.InvalidDestination=Choose a new or empty writable folder on a fixed local drive, without links or junctions.
it.ExistingDestination=L'installazione registrata non è valida. Disinstallare conservando i dati e reinstallare.
en.ExistingDestination=The registered installation is invalid. Uninstall while keeping data, then reinstall.
it.KeepDestination=Un aggiornamento deve usare la cartella già installata. Per spostare l'app, disinstallarla conservando i dati e reinstallarla.
en.KeepDestination=An update must use the installed folder. To move the app, uninstall while keeping data and reinstall.
it.NoSpace=Spazio insufficiente sul disco di destinazione.
en.NoSpace=Not enough free space on the destination drive.
it.SummaryVersion=Versione
en.SummaryVersion=Version
it.SummaryDestination=Cartella dell'app
en.SummaryDestination=Application folder
it.SummaryUser=Installazione per l'utente corrente
en.SummaryUser=Install for the current user
it.SummarySpace=Spazio richiesto
en.SummarySpace=Space required
it.SummaryStart=Collegamento nel menu Start
en.SummaryStart=Start menu shortcut
it.SummaryDesktop=Collegamento sul desktop
en.SummaryDesktop=Desktop shortcut
it.SummaryData=Indici e preferenze (non spostati dalla scelta della cartella dell'app)
en.SummaryData=Indexes and preferences (unaffected by the app folder choice)
it.Yes=Sì
en.Yes=Yes
it.No=No
en.No=No
it.LaunchApp=Avvia Local Document Search
en.LaunchApp=Launch Local Document Search
it.Downgrade=È già installata una versione più recente. Il downgrade è bloccato.
en.Downgrade=A newer version is already installed. Downgrade is blocked.
it.CloseForUninstall=Chiudere Local Document Search prima della disinstallazione.
en.CloseForUninstall=Close Local Document Search before uninstalling.
it.DeleteData=Eliminare indici e preferenze di Local Document Search? L'operazione non può essere annullata.
en.DeleteData=Delete Local Document Search indexes and preferences? This cannot be undone.
it.CleanupFailed=La pulizia dei dati è fallita. Chiudere l'applicazione e riprovare.
en.CleanupFailed=Data cleanup failed. Close the application and retry.
it.UpgradeFailed=Impossibile eliminare i vecchi file applicativi. Riprovare l'installer.
en.UpgradeFailed=Old application files could not be removed. Retry the installer.
it.LegacyInstall=Disinstallare prima la precedente installazione di Local Document Search conservando indici e preferenze, poi eseguire nuovamente questo installer. Al primo avvio occorre scegliere la cartella e indicizzarla nuovamente.
en.LegacyInstall=First uninstall the previous installation of Local Document Search, keeping indexes and preferences, then run this installer again. On first launch, select your folder and index it again.

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; Flags: unchecked

[Files]
Source: "{#PayloadDir}\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "{#SourcePath}\uninstall-data.ps1"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourcePath}\prune-upgrade.ps1"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourcePath}\prune-upgrade.ps1"; Flags: dontcopy

[Icons]
Name: "{autoprograms}\Local Document Search"; Filename: "{app}\LocalDocumentSearch.exe"
Name: "{autodesktop}\Local Document Search"; Filename: "{app}\LocalDocumentSearch.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\LocalDocumentSearch.exe"; Description: "{cm:LaunchApp}"; Flags: postinstall nowait skipifsilent

[Code]
const RunningMutex = 'Local\LocalDocumentSearchV2Running';
var DeleteData: Boolean;
    PreviousManifest, RegisteredPath: String;
    HasInstallation: Boolean;

function GetDriveTypeW(RootPathName: String): Integer;
  external 'GetDriveTypeW@kernel32.dll stdcall';
function GetFileAttributesW(FileName: String): Cardinal;
  external 'GetFileAttributesW@kernel32.dll stdcall';

function SamePath(A, B: String): Boolean;
begin
  Result := CompareText(RemoveBackslashUnlessRoot(ExpandFileName(A)),
    RemoveBackslashUnlessRoot(ExpandFileName(B))) = 0;
end;

function InsidePath(Path, Parent: String): Boolean;
var P, Q: String;
begin
  P := AddBackslash(RemoveBackslashUnlessRoot(ExpandFileName(Path)));
  Q := AddBackslash(RemoveBackslashUnlessRoot(ExpandFileName(Parent)));
  Result := CompareText(Copy(P, 1, Length(Q)), Q) = 0;
end;

function CheckDestination(Path: String; Existing: Boolean): String;
var Root, Ancestor, Probe: String;
    FindRec: TFindRec;
    FreeBytes, TotalBytes: Int64;
begin
  Result := ExpandConstant('{cm:InvalidDestination}');
  if Length(Path) < 4 then Exit;
  if (Path[2] <> ':') or (Path[3] <> '\') or
     (Pos('"', Path) > 0) or SamePath(Path, ExtractFileDrive(Path) + '\') then Exit;
  Root := ExtractFileDrive(Path) + '\';
  if GetDriveTypeW(Root) <> 3 then Exit;
  if InsidePath(Path, ExpandConstant('{localappdata}\LocalDocumentSearch')) or
     InsidePath(ExpandConstant('{localappdata}\LocalDocumentSearch'), Path) or
     InsidePath(Path, ExpandConstant('{localappdata}\LocalDocumentSearchV2')) or
     InsidePath(ExpandConstant('{localappdata}\LocalDocumentSearchV2'), Path) then Exit;
  Ancestor := RemoveBackslashUnlessRoot(ExpandFileName(Path));
  while not DirExists(Ancestor) do begin
    if FileExists(Ancestor) then Exit;
    Ancestor := ExtractFileDir(Ancestor);
    if Length(Ancestor) < 3 then Exit;
  end;
  Probe := Ancestor;
  while True do begin
    if (GetFileAttributesW(Ancestor) and $400) <> 0 then Exit;
    if SamePath(Ancestor, Root) then Break;
    Ancestor := ExtractFileDir(Ancestor);
  end;
  if Existing then begin
    if not DirExists(Path) or not FileExists(AddBackslash(Path) + 'LocalDocumentSearch.exe') then Exit;
  end else if DirExists(Path) then begin
    if FindFirst(AddBackslash(Path) + '*', FindRec) then begin
      try
        repeat
          if (FindRec.Name <> '.') and (FindRec.Name <> '..') then Exit;
        until not FindNext(FindRec);
      finally FindClose(FindRec); end;
    end;
  end;
  if DirExists(Path) then Probe := Path;
  if not GetSpaceOnDisk64(Probe, FreeBytes, TotalBytes) then Exit;
  if FreeBytes < StrToInt64('{#RequiredBytes}') then begin
    Result := ExpandConstant('{cm:NoSpace}'); Exit;
  end;
  Probe := AddBackslash(Probe) + 'lds-install-probe-' +
    Copy(GetSHA256OfUnicodeString(ExpandConstant('{tmp}')), 1, 16) + '.tmp';
  if not SaveStringToFile(Probe, '', False) then Exit;
  DeleteFile(Probe);
  Result := '';
end;

function CheckRunning: Boolean;
begin
  Result := True;
  while CheckForMutexes(RunningMutex) do begin
    Log(ExpandConstant('{cm:CloseForInstall}'));
    if WizardSilent then begin Result := False; Exit; end;
    if MsgBox(ExpandConstant('{cm:CloseForInstall}'), mbError, MB_RETRYCANCEL) <> IDRETRY then begin
      Result := False; Exit;
    end;
  end;
end;

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
var Installed, InstalledPath, Key: String;
begin
  Result := False;
  Key := 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{#RegistryId}_is1';
  if (RegQueryStringValue(HKCU, 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{#RegistryId}_is1', 'InstallLocation', InstalledPath) and
      (CompareText(RemoveBackslashUnlessRoot(InstalledPath), ExpandConstant('{localappdata}\Programs\LocalDocumentSearchV2')) = 0)) or
     FileExists(ExpandConstant('{localappdata}\Programs\LocalDocumentSearchV2\LocalDocumentSearch.exe')) then begin
    Log(ExpandConstant('{cm:LegacyInstall}'));
    if not WizardSilent then MsgBox(ExpandConstant('{cm:LegacyInstall}'), mbError, MB_OK);
    Exit;
  end;
  if not CheckRunning then Exit;
  if RegQueryStringValue(HKCU, Key, 'DisplayVersion', Installed) and
     OlderVersion(Installed, '{#AppVersion}') then begin
    if not WizardSilent then MsgBox(ExpandConstant('{cm:Downgrade}'), mbError, MB_OK);
    Exit;
  end;
  HasInstallation := RegKeyExists(HKCU, Key);
  if HasInstallation then begin
    if not RegQueryStringValue(HKCU, Key, 'InstallLocation', InstalledPath) or
       (InstalledPath = '') or (CheckDestination(InstalledPath, True) <> '') then begin
      Log(ExpandConstant('{cm:ExistingDestination}'));
      if not WizardSilent then MsgBox(ExpandConstant('{cm:ExistingDestination}'), mbError, MB_OK);
      Exit;
    end;
    RegisteredPath := InstalledPath;
    if (ExpandConstant('{param:DIR|}') <> '') and
       not SamePath(ExpandConstant('{param:DIR|}'), RegisteredPath) then begin
      Log(ExpandConstant('{cm:KeepDestination}'));
      if not WizardSilent then MsgBox(ExpandConstant('{cm:KeepDestination}'), mbError, MB_OK);
      Exit;
    end;
  end;
  Result := True;
end;

procedure InitializeWizard;
begin
  if HasInstallation then WizardForm.DirEdit.Text := RegisteredPath;
end;

function ShouldSkipPage(PageID: Integer): Boolean;
begin
  Result := HasInstallation and (PageID = wpSelectDir);
end;

function ValidateSelectedDestination: Boolean;
var ErrorText: String;
begin
  Result := False;
  if HasInstallation and not SamePath(WizardDirValue, RegisteredPath) then
    ErrorText := ExpandConstant('{cm:KeepDestination}')
  else ErrorText := CheckDestination(WizardDirValue, HasInstallation);
  if ErrorText <> '' then begin
    Log(ErrorText);
    if not WizardSilent then MsgBox(ErrorText, mbError, MB_OK);
    Exit;
  end;
  Result := True;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if CurPageID = wpSelectDir then Result := ValidateSelectedDestination;
end;

function UpdateReadyMemo(Space, NewLine, MemoUserInfoInfo, MemoDirInfo,
  MemoTypeInfo, MemoComponentsInfo, MemoGroupInfo, MemoTasksInfo: String): String;
var Desktop: String;
begin
  Desktop := ExpandConstant('{cm:No}');
  if WizardIsTaskSelected('desktopicon') then Desktop := ExpandConstant('{cm:Yes}');
  Result := ExpandConstant('{cm:SummaryVersion}') + ': {#AppVersion}' + NewLine +
    ExpandConstant('{cm:SummaryUser}') + NewLine +
    ExpandConstant('{cm:SummaryDestination}') + ': ' + WizardDirValue + NewLine +
    ExpandConstant('{cm:SummarySpace}') + ': ' + WizardForm.DiskSpaceLabel.Caption + NewLine +
    ExpandConstant('{cm:SummaryStart}') + ': ' + ExpandConstant('{cm:Yes}') + NewLine +
    ExpandConstant('{cm:SummaryDesktop}') + ': ' + Desktop + NewLine +
    ExpandConstant('{cm:SummaryData}') + ': ' +
      ExpandConstant('{localappdata}\LocalDocumentSearch\Data');
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
    if not ValidateSelectedDestination or not CheckRunning then Abort;
    Root := ExpandConstant('{app}');
    PreviousManifest := ExpandConstant('{tmp}\previous-build-manifest.json');
    if HasInstallation and not FileExists(Root + '\BUILD-MANIFEST.json') then
      RaiseException(ExpandConstant('{cm:UpgradeFailed}'));
    if FileExists(Root + '\BUILD-MANIFEST.json') and
       not CopyFile(Root + '\BUILD-MANIFEST.json', PreviousManifest, False) then
      RaiseException(ExpandConstant('{cm:UpgradeFailed}'));
    if FileExists(PreviousManifest) then begin
      ExtractTemporaryFile('prune-upgrade.ps1');
      Script := ExpandConstant('{tmp}\prune-upgrade.ps1');
      if not Exec(ExpandConstant('{sys}\WindowsPowerShell\v1.0\powershell.exe'),
        '-NoProfile -NonInteractive -ExecutionPolicy Bypass -File "' + Script +
        '" -InstallRoot "' + Root + '" -PreviousManifest "' + PreviousManifest + '" -ValidateOnly',
        '', SW_HIDE, ewWaitUntilTerminated, ExitCode) or (ExitCode <> 0) then
        RaiseException(ExpandConstant('{cm:UpgradeFailed}'));
    end;
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
