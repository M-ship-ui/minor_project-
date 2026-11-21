@echo off
title Open Project in VS Code - Sanskriti University
echo Launching VS Code with single_file_academic_system.py ...
cd /d "%~dp0"
start "" "C:\Users\bandi\AppData\Local\Programs\Microsoft VS Code\Code.exe" "%~dp0" "%~dp0single_file_academic_system.py" "%~dp0REPORT_COMPLETION_DATA.md" "%~dp0matching.py"
