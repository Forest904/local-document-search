# Native API per tokenizzare CommandLine e chiudere anche finestre nascoste.
if (-not ('LdsDev.Windows' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;
namespace LdsDev {
    public static class Windows {
        [DllImport("shell32.dll", SetLastError=true)]
        static extern IntPtr CommandLineToArgvW([MarshalAs(UnmanagedType.LPWStr)] string cmd, out int count);
        [DllImport("kernel32.dll")] static extern IntPtr LocalFree(IntPtr p);
        delegate bool EnumCallback(IntPtr window, IntPtr data);
        [DllImport("user32.dll")] static extern bool EnumWindows(EnumCallback callback, IntPtr data);
        [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr window, out uint pid);
        [DllImport("user32.dll", CharSet=CharSet.Unicode)] static extern int GetWindowText(IntPtr window, StringBuilder text, int max);
        [DllImport("user32.dll")] static extern bool PostMessage(IntPtr window, uint msg, IntPtr w, IntPtr l);
        public static string[] Arguments(string command) {
            int count;
            IntPtr p = CommandLineToArgvW(command, out count);
            if (p == IntPtr.Zero) return new string[0];
            try {
                var result = new string[count];
                for (int i=0; i<count; i++) result[i] = Marshal.PtrToStringUni(Marshal.ReadIntPtr(p, i*IntPtr.Size));
                return result;
            } finally { LocalFree(p); }
        }
        public static bool Window(uint pid, bool close) {
            bool found = false;
            EnumWindows((window, data) => {
                uint owner;
                GetWindowThreadProcessId(window, out owner);
                if (owner == pid) {
                    var title = new StringBuilder(1024);
                    GetWindowText(window, title, title.Capacity);
                    if (title.ToString() == "Local Document Search") {
                        found = true;
                        if (close) PostMessage(window, 0x0010, IntPtr.Zero, IntPtr.Zero);
                    }
                }
                return true;
            }, IntPtr.Zero);
            return found;
        }
    }
}
'@
}

function Test-DesktopCommand([string]$CommandLine, [string]$Repository) {
    if (-not $CommandLine) { return $false }
    $arguments = [LdsDev.Windows]::Arguments($CommandLine)
    $wrapper = [IO.Path]::GetFullPath((Join-Path $Repository 'scripts/dev/run_desktop.py'))
    if ($arguments.Length -gt 1 -and $arguments[1] -eq $wrapper) { return $true }
    if ($arguments.Length -gt 2 -and $arguments[1] -eq '-m' -and
        $arguments[2] -eq 'local_document_search_desktop.main') { return $true }
    # Il launcher console/gui puo essere diretto oppure figlio del redirector Python.
    foreach ($argument in ($arguments | Select-Object -First 2)) {
        try {
            if ([IO.Path]::GetFileName($argument) -eq 'local-document-search-desktop.exe') { return $true }
        } catch [ArgumentException] { }
    }
    return $false
}

function Get-DesktopProcesses([string]$Repository) {
    $sid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
    Get-CimInstance Win32_Process | Where-Object {
        $_.Name -match '^(pythonw?|local-document-search-desktop)\.exe$' -and
        (Test-DesktopCommand $_.CommandLine $Repository)
    } | Where-Object {
        (Invoke-CimMethod -InputObject $_ -MethodName GetOwnerSid).Sid -eq $sid
    }
}

function Get-SameProcess($Original) {
    $current = Get-CimInstance Win32_Process -Filter "ProcessId = $($Original.ProcessId)"
    if ($current -and $current.CreationDate -eq $Original.CreationDate -and
        $current.CommandLine -eq $Original.CommandLine) { return $current }
}
