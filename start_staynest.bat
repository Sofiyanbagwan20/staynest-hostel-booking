@echo off
title StayNest Server & Frontend
cd /d "%~dp0backend"
echo ===================================================
echo           Starting StayNest Fullstack App
echo ===================================================
echo Opening StayNest in your browser...
start http://127.0.0.1:5000
echo.
echo Server running on http://127.0.0.1:5000
echo Keep this window open while using StayNest.
echo Press Ctrl+C to stop.
echo ===================================================
python app.py
pause
