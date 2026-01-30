@echo off
REM Telegram Multi-Account Message Sender Launcher
REM This batch file ensures the application runs regardless of PATH configuration

setlocal enabledelayedexpansion

echo Starting Telegram Multi-Account Message Sender...
echo.

REM Method 1: Try running main.py in current directory (development mode)
if exist "main.py" (
    echo Running from source directory...
    python main.py
    if !ERRORLEVEL! EQU 0 exit /b 0
)

REM Method 2: Try running as Python module (installed via pip)
python -m app.cli >nul 2>&1
if !ERRORLEVEL! EQU 0 (
    echo Running as Python module...
    python -m app.cli
    exit /b 0
)

REM Method 3: Try to find executable in Python Scripts directories
set "FOUND=0"
for /d %%P in ("%LOCALAPPDATA%\Programs\Python\Python*") do (
    if exist "%%P\Scripts\telegram-multi-account-sender.exe" (
        echo Found executable in: %%P\Scripts
        "%%P\Scripts\telegram-multi-account-sender.exe"
        set "FOUND=1"
        exit /b 0
    )
)

REM Method 4: Try AppData\Roaming\Python (user installs)
for /d %%P in ("%APPDATA%\Python\Python*") do (
    if exist "%%P\Scripts\telegram-multi-account-sender.exe" (
        echo Found executable in: %%P\Scripts
        "%%P\Scripts\telegram-multi-account-sender.exe"
        set "FOUND=1"
        exit /b 0
    )
)

REM Method 5: Try common Python installation paths
for %%P in (
    "%ProgramFiles%\Python*"
    "%ProgramFiles(x86)%\Python*"
    "%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe"
) do (
    if exist "%%P\Scripts\telegram-multi-account-sender.exe" (
        echo Found executable in: %%P\Scripts
        "%%P\Scripts\telegram-multi-account-sender.exe"
        set "FOUND=1"
        exit /b 0
    )
)

REM If all methods failed, show error message
echo.
echo ========================================
echo ERROR: Could not start the application
echo ========================================
echo.
echo The application could not be found. Please try one of these solutions:
echo.
echo 1. Install from source:
echo    - Ensure Python 3.10+ is installed
echo    - Run: pip install -r requirements.txt
echo    - Run: python main.py
echo.
echo 2. Install via pip:
echo    - Run: pip install telegram-multi-account-sender
echo    - Run: python -m app.cli
echo.
echo 3. Download Windows executable:
echo    - Visit: https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender/releases
echo    - Download the latest .exe installer
echo.
echo 4. Check Python installation:
echo    - Run: python --version
echo    - Ensure Python 3.10+ is installed and in PATH
echo.
pause
exit /b 1
