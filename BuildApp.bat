@echo off
setlocal

REM Use venv's Python/PyInstaller if available
if exist ".venv\Scripts\python.exe" (
    set PYTHON_CMD=.venv\Scripts\python.exe
    set PYINSTALLER_CMD=.venv\Scripts\pyinstaller.exe
) else (
    set PYTHON_CMD=python
    set PYINSTALLER_CMD=pyinstaller
)

echo Building Earthward Analyzer...
echo.

REM Check if spec file exists
if exist "EarthwardAnalyzer.spec" (
    echo Using optimized spec file for faster rebuild
    echo.
    %PYINSTALLER_CMD% EarthwardAnalyzer.spec
) else (
    echo Creating spec file for first build
    echo This will take longer on first run
    echo.
    %PYINSTALLER_CMD% --onefile --windowed --name "EarthwardAnalyzer" --paths . --paths .\Configuration --paths .\Tabs --paths .\SQLHelper --hidden-import tkinterdnd2 --hidden-import matplotlib.backends.backend_tkagg --hidden-import tkinter --hidden-import _tkinter --exclude-module numpy.distutils --exclude-module PyQt5 --exclude-module PySide6 main.py
)

echo.
echo Build complete! Check the dist folder.
pause