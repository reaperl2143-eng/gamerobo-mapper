@echo off
title GameRobo RH-5188 -> Xbox 360
cd /d "%~dp0"
python ds2xinput.py
echo.
echo Mapper stopped. Press any key to close.
pause >nul
