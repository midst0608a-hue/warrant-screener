@echo off
title Update Warrants Data
chcp 65001 >nul
echo =========================================
echo.
echo    Fetching latest data from TWSE/TPEx...
echo.
echo =========================================
cd /d "%~dp0"
python fetch_warrants.py

echo.
echo =========================================
echo.
echo    Fetch complete! Syncing with GitHub...
echo.
echo =========================================
git add warrants_data.json
git commit -m "Auto-update warrants data"
git push

echo.
echo =========================================
echo.
echo    Warrants Data Update SUCCESS!
echo.
echo =========================================
if "%1"=="--scheduled" goto end
if "%1"=="/silent" goto end
if "%1"=="--no-pause" goto end
pause
:end
