@echo off
REM AEGIS-DocIntel Evaluation Client Launcher Batch File
setlocal
set "SCRIPT_DIR=%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%AEGIS-DocIntel.ps1" %*
endlocal
