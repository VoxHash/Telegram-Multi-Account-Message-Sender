# Install the frozen Windows EXE and register *.tmas-backup.zip file association
# for the current user (HKCU). No administrator rights required.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File .\install.ps1
#   powershell -ExecutionPolicy Bypass -File .\install.ps1 -Uninstall
#   powershell -ExecutionPolicy Bypass -File .\install.ps1 -ExePath "D:\path\to\telegram-multi-account-sender.exe"
#
# File association: double-click *.tmas-backup.zip to open a local restore prompt.

[CmdletBinding()]
param(
    [switch]$Uninstall,
    [string]$InstallDir = "",
    [string]$ExePath = ""
)

$ErrorActionPreference = "Stop"

$AppName = "Telegram Multi-Account Message Sender"
$ExeName = "telegram-multi-account-sender.exe"
$ProgId = "dev.voxhash.tmas-backup"
$Extension = ".tmas-backup.zip"
$FriendlyTypeName = "TMAS Backup Package"
$ClassesRoot = "HKCU:\Software\Classes"

if (-not $InstallDir) {
    $InstallDir = Join-Path $env:LOCALAPPDATA "Programs\TelegramMultiAccountSender"
}

function Write-Usage {
    @"
Usage: .\install.ps1 [-InstallDir DIR] [-ExePath PATH] [-Uninstall]

Installs $ExeName into a per-user Programs folder and registers
$Extension -> $ProgId (open with the installed EXE).

Options:
  -InstallDir DIR   Install directory (default: %LOCALAPPDATA%\Programs\TelegramMultiAccountSender)
  -ExePath PATH     Associate an existing EXE without copying (portable / associate-only)
  -Uninstall        Remove association + installed EXE (leaves -ExePath targets alone)
"@
}

function Invoke-ShellNotify {
    Add-Type -Namespace TMAS.Packaging -Name ShellNotify -MemberDefinition @"
using System;
using System.Runtime.InteropServices;
public static class NativeMethods {
    [DllImport("shell32.dll")]
    public static extern void SHChangeNotify(int wEventId, uint uFlags, IntPtr dwItem1, IntPtr dwItem2);
}
"@ -ErrorAction SilentlyContinue
    try {
        [TMAS.Packaging.ShellNotify.NativeMethods]::SHChangeNotify(0x08000000, 0x0000, [IntPtr]::Zero, [IntPtr]::Zero)
    } catch {
        # Best-effort; association still written to the registry.
    }
}

function Remove-FileAssociation {
    $progPath = Join-Path $ClassesRoot $ProgId
    if (Test-Path $progPath) {
        Remove-Item -Path $progPath -Recurse -Force
    }

    $extPath = Join-Path $ClassesRoot $Extension
    if (Test-Path $extPath) {
        $current = (Get-ItemProperty -Path $extPath -Name "(default)" -ErrorAction SilentlyContinue)."(default)"
        if ($current -eq $ProgId) {
            Remove-ItemProperty -Path $extPath -Name "(default)" -ErrorAction SilentlyContinue
        }
        $owPath = Join-Path $extPath "OpenWithProgids"
        if (Test-Path $owPath) {
            Remove-ItemProperty -Path $owPath -Name $ProgId -ErrorAction SilentlyContinue
        }
        # Remove empty extension key tree when we created it solely for TMAS.
        $children = @(Get-ChildItem -Path $extPath -ErrorAction SilentlyContinue)
        $props = @(Get-ItemProperty -Path $extPath -ErrorAction SilentlyContinue |
            Get-Member -MemberType NoteProperty |
            Where-Object { $_.Name -notin @("PSPath", "PSParentPath", "PSChildName", "PSDrive", "PSProvider") })
        if ($children.Count -eq 0 -and $props.Count -eq 0) {
            Remove-Item -Path $extPath -Recurse -Force -ErrorAction SilentlyContinue
        }
    }

    Invoke-ShellNotify
}

function Uninstall-App {
    Remove-FileAssociation

    $installedExe = Join-Path $InstallDir $ExeName
    if (Test-Path $installedExe) {
        Remove-Item -Force $installedExe
    }
    if ((Test-Path $InstallDir) -and -not (Get-ChildItem -Force $InstallDir -ErrorAction SilentlyContinue)) {
        Remove-Item -Force $InstallDir
    }

    Write-Host "Uninstalled $AppName association from HKCU and removed $installedExe (if present)."
}

function Resolve-SourceExe {
    if ($ExePath) {
        $resolved = [System.IO.Path]::GetFullPath($ExePath)
        if (-not (Test-Path -LiteralPath $resolved -PathType Leaf)) {
            throw "error: -ExePath not found: $resolved"
        }
        return $resolved
    }

    $beside = Join-Path $PSScriptRoot $ExeName
    if (Test-Path -LiteralPath $beside -PathType Leaf) {
        return (Resolve-Path -LiteralPath $beside).Path
    }

    $distCandidate = Join-Path $PSScriptRoot "..\..\dist\$ExeName"
    if (Test-Path -LiteralPath $distCandidate -PathType Leaf) {
        return (Resolve-Path -LiteralPath $distCandidate).Path
    }

    throw "error: $ExeName not found next to install.ps1 (assemble a release dir with packaging/windows/assemble-dist.sh first, or pass -ExePath)."
}

function Register-FileAssociation {
    param([Parameter(Mandatory = $true)][string]$TargetExe)

    $progPath = Join-Path $ClassesRoot $ProgId
    New-Item -Path $progPath -Force | Out-Null
    Set-ItemProperty -Path $progPath -Name "(default)" -Value $FriendlyTypeName

    $iconPath = Join-Path $progPath "DefaultIcon"
    New-Item -Path $iconPath -Force | Out-Null
    Set-ItemProperty -Path $iconPath -Name "(default)" -Value "`"$TargetExe`",0"

    $cmdPath = Join-Path $progPath "shell\open\command"
    New-Item -Path $cmdPath -Force | Out-Null
    Set-ItemProperty -Path $cmdPath -Name "(default)" -Value "`"$TargetExe`" `"%1`""

    $extPath = Join-Path $ClassesRoot $Extension
    New-Item -Path $extPath -Force | Out-Null
    Set-ItemProperty -Path $extPath -Name "(default)" -Value $ProgId

    $owPath = Join-Path $extPath "OpenWithProgids"
    New-Item -Path $owPath -Force | Out-Null
    # Empty string marks the ProgID as an Open With candidate (REG_SZ).
    New-ItemProperty -Path $owPath -Name $ProgId -Value "" -PropertyType String -Force | Out-Null

    Invoke-ShellNotify
}

if ($Uninstall) {
    Uninstall-App
    exit 0
}

$sourceExe = Resolve-SourceExe

if ($ExePath) {
    $targetExe = $sourceExe
} else {
    New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
    $targetExe = Join-Path $InstallDir $ExeName
    Copy-Item -LiteralPath $sourceExe -Destination $targetExe -Force
}

Register-FileAssociation -TargetExe $targetExe

Write-Host "Installed $AppName"
Write-Host "  EXE:     $targetExe"
Write-Host "  ProgID:  $ProgId"
Write-Host "  Ext:     *$Extension"
Write-Host ""
Write-Host "Double-click a *$Extension file to open a local restore prompt."
Write-Host "Uninstall: powershell -ExecutionPolicy Bypass -File .\install.ps1 -Uninstall"
