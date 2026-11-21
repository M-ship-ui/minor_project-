@echo off
title Sanskriti University - Academic Asset Portal (Live Website Launcher)
color 0B
cd /d "%~dp0"
start "Sanskriti Recovery Server (Port 5000)" python app.py
timeout /t 3 /nobreak >nul
start http://127.0.0.1:5000
start "Cloudflare Live Public Tunnel" "C:\Users\bandi\AppData\Local\Programs\cloudflared.exe" tunnel --url http://127.0.0.1:5000
