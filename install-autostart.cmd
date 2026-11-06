@echo off
title GameRobo Mapper - PC setup
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install-autostart.ps1"
echo.
echo Done. Press any key to close.
pause >nul
