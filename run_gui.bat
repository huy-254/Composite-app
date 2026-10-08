@echo off
REM Composite Ply Properties Calculator GUI
REM Chạy chương trình Python GUI

cd /d "%~dp0"
python gui_ply.py

if errorlevel 1 (
    echo Error: Could not run gui_ply.py
    echo Make sure Python is installed and in PATH
    echo Or run: python gui_ply.py
    pause
)
