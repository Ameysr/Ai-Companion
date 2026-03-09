@echo off
title AI Coach - Install Background Notifier
echo.
echo  ================================================
echo    AI Coach - Install Background Notifier
echo  ================================================
echo.
echo  This will make AI Coach start automatically
echo  when your computer turns on. It runs silently
echo  in the system tray and sends you notifications.
echo.

:: Get the startup folder path
set STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup

:: Get current directory
set APP_DIR=%~dp0

:: Create a VBS script that runs the notifier silently (no terminal window)
echo Creating startup script...

(
echo Set WshShell = CreateObject("WScript.Shell"^)
echo WshShell.Run "pythonw ""%APP_DIR%notifier_bg.py""", 0, False
) > "%STARTUP%\ai_coach_notifier.vbs"

echo.
echo  [OK] Background notifier installed!
echo.
echo  What happens now:
echo    - Every time your PC starts, AI Coach runs silently
echo    - You'll see a small white dot in your system tray
echo    - Right-click it to open the full app or quit
echo    - Notifications every %NUDGE_INTERVAL% hours (default: 3)
echo.
echo  To uninstall: delete ai_coach_notifier.vbs from
echo    %STARTUP%
echo.
pause
