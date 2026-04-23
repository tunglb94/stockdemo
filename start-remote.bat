@echo off
title StockSim Remote Launcher
color 0B
cls

echo.
echo  =====================================================
echo   STOCKSIM - Remote Access Mode (Cloudflare Tunnel)
echo  =====================================================
echo.

cd /d %~dp0

REM === Dung env public thay vi localhost ===
echo [0/4] Cai dat env cho remote access...
copy /Y frontend\.env.tunnel frontend\.env.local >nul
echo     Done! API: https://api.nankybeauty.com

REM === BACKEND SETUP ===
echo [1/4] Kiem tra va setup backend...
cd backend
call venv\Scripts\activate.bat
python manage.py migrate --run-syncdb 2>nul
python manage.py create_bots 2>nul
python manage.py create_crypto_bots 2>nul
python manage.py create_futures_bots 2>nul
cd ..

REM === START BACKEND ===
echo [2/4] Khoi dong Django backend (port 8000)...
start "StockSim Backend" cmd /k "cd /d %~dp0backend && call venv\Scripts\activate.bat && python manage.py runserver"
timeout /t 3 /nobreak >nul

REM === START MARKET FEED ===
echo [3/4] Khoi dong Market Feed + AI Bot Scheduler...
start "StockSim Market Feed" cmd /k "cd /d %~dp0backend && call venv\Scripts\activate.bat && python manage.py run_market_feed"

REM === START FRONTEND ===
echo [4/4] Khoi dong Frontend (port 3000)...
start "StockSim Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"
timeout /t 8 /nobreak >nul

REM === START CLOUDFLARE TUNNEL ===
echo [5/4] Khoi dong Cloudflare Tunnel...
start "Cloudflare Tunnel" cmd /k "%USERPROFILE%\cloudflared.exe tunnel run stocksim"

echo.
echo  =====================================================
echo   REMOTE MODE DA CHAY!
echo.
echo   Truy cap tu cong ty (Mac):
echo     https://stock.nankybeauty.com
echo.
echo   Truy cap tai nha:
echo     http://localhost:3000
echo  =====================================================
echo.
pause
