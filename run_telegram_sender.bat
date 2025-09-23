@echo off
REM Telegram Multi-Account Message Sender Launcher
REM This batch file ensures the application runs regardless of PATH configuration

echo Starting Telegram Multi-Account Message Sender...

REM Try to find the executable in common locations
if exist "C:\Users\%USERNAME%\AppData\Roaming\Python\Python313\Scripts\telegram-multi-account-sender.exe" (
    "C:\Users\%USERNAME%\AppData\Roaming\Python\Python313\Scripts\telegram-multi-account-sender.exe"
    goto :end
)

if exist "C:\Users\%USERNAME%\AppData\Roaming\Python\Python312\Scripts\telegram-multi-account-sender.exe" (
    "C:\Users\%USERNAME%\AppData\Roaming\Python\Python312\Scripts\telegram-multi-account-sender.exe"
    goto :end
)

if exist "C:\Users\%USERNAME%\AppData\Roaming\Python\Python311\Scripts\telegram-multi-account-sender.exe" (
    "C:\Users\%USERNAME%\AppData\Roaming\Python\Python311\Scripts\telegram-multi-account-sender.exe"
    goto :end
)

REM Try to run via Python module
python -m app.cli
if %ERRORLEVEL% EQU 0 goto :end

REM If all else fails, show error
echo.
echo ERROR: Could not find Telegram Multi-Account Message Sender
echo.
echo Please try one of these solutions:
echo 1. Download the Windows executable from:
echo    https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender/releases
echo.
echo 2. Add Python Scripts to your PATH:
echo    C:\Users\%USERNAME%\AppData\Roaming\Python\Python313\Scripts
echo.
echo 3. Run directly with: python -m app.cli
echo.
pause

:end
