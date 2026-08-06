@echo off
title 權證篩選器伺服器
echo =========================================
echo.
echo    正在啟動權證篩選器，請稍候...
echo.
echo =========================================
cd /d "%~dp0"
python -m streamlit run warrant_screener_app.py
pause
