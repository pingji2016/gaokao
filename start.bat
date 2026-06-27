@echo off
echo ============================================
echo   安徽高考数据查询系统
echo   GAOKAO Data Query System
echo ============================================
echo.
echo Starting server at http://localhost:5000
echo Press Ctrl+C to stop
echo.

cd /d "%~dp0"
python server.py

pause
