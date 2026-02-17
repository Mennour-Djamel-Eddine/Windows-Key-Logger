@echo off
REM Change to project root
cd /d "%~dp0\.."

echo ========================================
echo PyLoggy - Stop Script
echo ========================================
echo.
echo Stopping keylogger...
echo.
echo Attempting to stop PyLoggy.exe...
taskkill /F /IM PyLoggy.exe 2>nul
if %errorlevel%==0 (
    echo PyLoggy.exe stopped successfully!
) else (
    echo PyLoggy.exe not found or already stopped.
)
echo.
echo Removing from startup registry...
echo Checking for registry entries...
reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" | findstr /i "Windows Security Update Microsoft System Service Windows Defender Service System Configuration Manager Windows Update Service" >nul
if %errorlevel%==0 (
    echo Found suspicious registry entries. Removing...
    reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "Windows Security Update" /f 2>nul
    reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "Microsoft System Service" /f 2>nul
    reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "Windows Defender Service" /f 2>nul
    reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "System Configuration Manager" /f 2>nul
    reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "Windows Update Service" /f 2>nul
    echo Registry entries removed.
) else (
    echo No suspicious registry entries found.
)
echo.
pause
