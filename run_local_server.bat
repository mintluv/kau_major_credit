@echo off
chcp 65001 > nul
title KAU GPA Calculator - Local Server

echo ========================================================
echo   🎓 한국항공대 전공 평점 계산기 (내 컴퓨터 로컬 서버)
echo ========================================================
echo.
echo [1/2] 로컬 백엔드 서버를 시작합니다... (http://127.0.0.1:8000)
echo.

start http://127.0.0.1:8000
python -m uvicorn app:app --host 127.0.0.1 --port 8000

pause
