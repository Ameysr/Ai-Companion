@echo off
title AI Coach - Install Background Notifier
echo.
echo  ================================================
echo    AI Coach - Install to Windows Startup
echo  ================================================
echo.

set STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
set APP_DIR=%~dp0

:: Copy the VBS launcher to startup folder
copy /Y "%APP_DIR%start_notifier.vbs" "%STARTUP%\ai_coach_notifier.vbs" >nul

:: But the startup copy needs the FULL path hardcoded
(
echo Set WshShell = CreateObject("WScript.Shell"^)
echo WshShell.Run "pythonw ""%APP_DIR%notifier_bg.py""", 0, False
) > "%STARTUP%\ai_coach_notifier.vbs"

echo.
echo  [OK] Installed! AI Coach will start automatically on boot.
echo.
echo  What happens:
echo    - PC starts = notifier runs silently in background
echo    - White dot in system tray (near clock)
echo    - Right-click tray icon = Open app or Quit
echo    - Notifications every 3 hours
echo.
echo  To uninstall, delete this file:
echo    %STARTUP%\ai_coach_notifier.vbs
echo.
pause
