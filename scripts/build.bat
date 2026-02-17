@echo off
REM Change to the project root directory
cd /d "%~dp0\.."

echo ========================================
echo PyLoggy Build Script
echo ========================================
echo.
echo Current directory: %CD%
echo.

echo Checking Python installation...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH!
    echo Please install Python first.
    pause
    exit /b 1
)

echo.
echo Installing PyInstaller...
python -m pip install pyinstaller --quiet

echo.
echo Building executable...
echo Source: src\PyLoggy.py
echo Output: output\PyLoggy.exe
echo.
python -m PyInstaller --onefile --windowed --name PyLoggy src\PyLoggy.py --clean --distpath output --workpath build

echo.
if exist "output\PyLoggy.exe" (
    echo.
    echo ========================================
    echo SUCCESS: Executable created!
    echo Location: %CD%\output\PyLoggy.exe
    echo ========================================
) else (
    echo.
    echo ERROR: Build failed! Check the output above for errors.
)
echo.
pause

