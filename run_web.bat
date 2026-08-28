@echo off
title GTU Alerts Web Dashboard Server
cd /d "%~dp0"

echo ========================================================
echo        GTU Alerts Live Web Dashboard Server
echo ========================================================
echo.
echo [i] Starting Web Server on http://127.0.0.1:8080 ...
echo [i] Browser will open automatically in 2 seconds...
echo.

start "" http://127.0.0.1:8080
python web_server.py

pause
