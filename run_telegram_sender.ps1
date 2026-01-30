# Telegram Multi-Account Message Sender Launcher (PowerShell)
# This script ensures the application runs regardless of PATH configuration
#
# Usage:
#   .\run_telegram_sender.ps1
#
# Note: PowerShell requires .\ prefix to run scripts from current directory
# If you get an execution policy error, run:
#   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

Write-Host "Starting Telegram Multi-Account Message Sender..." -ForegroundColor Cyan
Write-Host ""

# Method 1: Try running main.py in current directory (development mode)
if (Test-Path "main.py") {
    Write-Host "Running from source directory..." -ForegroundColor Green
    python main.py
    if ($LASTEXITCODE -eq 0) { exit 0 }
}

# Method 2: Try running as Python module (installed via pip)
try {
    python -m app.cli 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Running as Python module..." -ForegroundColor Green
        python -m app.cli
        exit 0
    }
} catch {
    # Continue to next method
}

# Method 3: Try to find executable in Python Scripts directories
$found = $false

# Check LocalAppData\Programs\Python
$pythonPaths = Get-ChildItem -Path "$env:LOCALAPPDATA\Programs\Python" -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -like "Python*" }
foreach ($pythonPath in $pythonPaths) {
    $exePath = Join-Path $pythonPath.FullName "Scripts\telegram-multi-account-sender.exe"
    if (Test-Path $exePath) {
        Write-Host "Found executable in: $exePath" -ForegroundColor Green
        & $exePath
        exit 0
    }
}

# Check AppData\Roaming\Python (user installs)
$pythonPaths = Get-ChildItem -Path "$env:APPDATA\Python" -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -like "Python*" }
foreach ($pythonPath in $pythonPaths) {
    $exePath = Join-Path $pythonPath.FullName "Scripts\telegram-multi-account-sender.exe"
    if (Test-Path $exePath) {
        Write-Host "Found executable in: $exePath" -ForegroundColor Green
        & $exePath
        exit 0
    }
}

# Check Program Files
$programPaths = @(
    "${env:ProgramFiles}\Python*",
    "${env:ProgramFiles(x86)}\Python*"
)

foreach ($pattern in $programPaths) {
    $pythonPaths = Get-ChildItem -Path $pattern -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -like "Python*" }
    foreach ($pythonPath in $pythonPaths) {
        $exePath = Join-Path $pythonPath.FullName "Scripts\telegram-multi-account-sender.exe"
        if (Test-Path $exePath) {
            Write-Host "Found executable in: $exePath" -ForegroundColor Green
            & $exePath
            exit 0
        }
    }
}

# If all methods failed, show error message
Write-Host ""
Write-Host "========================================" -ForegroundColor Red
Write-Host "ERROR: Could not start the application" -ForegroundColor Red
Write-Host "========================================" -ForegroundColor Red
Write-Host ""
Write-Host "The application could not be found. Please try one of these solutions:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Install from source:" -ForegroundColor Cyan
Write-Host "   - Ensure Python 3.10+ is installed"
Write-Host "   - Run: pip install -r requirements.txt"
Write-Host "   - Run: python main.py"
Write-Host ""
Write-Host "2. Install via pip:" -ForegroundColor Cyan
Write-Host "   - Run: pip install telegram-multi-account-sender"
Write-Host "   - Run: python -m app.cli"
Write-Host ""
Write-Host "3. Download Windows executable:" -ForegroundColor Cyan
Write-Host "   - Visit: https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender/releases"
Write-Host "   - Download the latest .exe installer"
Write-Host ""
Write-Host "4. Check Python installation:" -ForegroundColor Cyan
Write-Host "   - Run: python --version"
Write-Host "   - Ensure Python 3.10+ is installed and in PATH"
Write-Host ""

Read-Host "Press Enter to exit"
exit 1

