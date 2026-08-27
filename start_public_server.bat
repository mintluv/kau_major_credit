@echo off
chcp 65001 > nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
title KAU GPA Calculator - Cloudflare Auto-Sync Launcher

python -X utf8 start_public_server.py
pause
