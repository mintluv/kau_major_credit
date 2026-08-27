@echo off
chcp 65001 > nul
title KAU GPA Calculator - Server & Cloudflare Tunnel

echo ========================================================
echo   🎓 한국항공대 전공 평점 계산기 (FastAPI + Cloudflare)
echo ========================================================
echo.

:: 1. Check cloudflared.exe
if not exist "cloudflared.exe" (
    echo [1/3] Cloudflare Tunnel 실행 파일(cloudflared.exe)을 다운로드합니다...
    powershell -Command "Invoke-WebRequest -Uri 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe' -OutFile 'cloudflared.exe'"
    if exist "cloudflared.exe" (
        echo [OK] 다운로드 완료!
    ) else (
        echo [ERROR] 다운로드 실패. 인터넷 연결을 확인하세요.
        pause
        exit /b 1
    )
) else (
    echo [1/3] cloudflared.exe 확인 완료.
)

echo.
echo [2/3] FastAPI 백엔드 서버를 백그라운드로 실행합니다...
start "KAU GPA Backend Server" cmd /k "python -m uvicorn app:app --host 127.0.0.1 --port 8000"

timeout /t 2 > nul

echo.
echo [3/3] Cloudflare Tunnel을 시작하여 외부 접속 URL을 생성합니다...
echo --------------------------------------------------------
echo   아래에 출력되는 [https://xxxxx.trycloudflare.com] 주소를
echo   GitHub Pages(https://mintluv.github.io/kau_major_credit)의
echo   [⚙️ 서버 연동] 메뉴에 입력하시면 어디서든 작동합니다!
echo --------------------------------------------------------
echo.

cloudflared.exe tunnel --url http://127.0.0.1:8000
pause
