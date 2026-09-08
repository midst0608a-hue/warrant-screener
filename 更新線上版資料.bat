@echo off
title Update Warrants Data
chcp 65001 >nul
echo =========================================
echo.
echo    Syncing repository with GitHub...
echo.
echo =========================================
cd /d "%~dp0"
git pull --rebase origin main --autostash

echo.
echo =========================================
echo.
echo    Fetching latest data from TWSE/TPEx...
echo.
echo =========================================
python fetch_warrants.py

echo.
echo =========================================
echo.
echo    Fetch complete! Syncing with GitHub...
echo.
echo =========================================
git add warrants_data.json
git diff --cached --quiet
if errorlevel 1 (
    git commit -m "Auto-update warrants data"
    git pull --rebase origin main --autostash
    git push origin main
) else (
    echo 資料無異動，無需推送到 GitHub。
)

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
