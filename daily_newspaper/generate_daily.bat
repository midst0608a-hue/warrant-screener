@echo off
chcp 65001 >nul
title 每日新聞報紙生成器 (Daily Newspaper Generator)

echo ========================================================
echo  📰 每日新聞報紙生成器 - 一鍵生成晨報
echo ========================================================
echo.

cd /d "%~dp0"

echo [1/3] 檢查並安裝必要套件...
pip install -r requirements.txt -q

echo.
echo [2/3] 正在抓取今日新聞並透過 Gemini 智慧排版...
python main.py

echo.
echo [3/3] 執行完成！
pause
