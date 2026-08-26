@echo off
title GTU Circular Telegram Automation
cd /d "%~dp0"

echo ========================================================
echo        GTU Circular Telegram Automation Bot
echo ========================================================
echo.

if not exist ".env" (
    echo [!] .env file nahi mili. Setup wizard start ho raha hai...
    echo.
    python setup_bot.py
) else (
    echo [i] Starting GTU Circular Daemon Monitor...
    python main.py --daemon
)

pause
