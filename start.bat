@echo off
title StockSim Launcher
color 0A
cls

echo.
echo  =====================================================
echo   STOCKSIM - Vietnam Stock Market Simulator
echo  =====================================================
echo.

cd /d %~dp0

REM === BACKEND SETUP ===
echo [1/4] Kiem tra va setup backend...
cd backend
call venv\Scripts\activate.bat

REM Chay migrations neu can (bao gom crypto app moi)
python manage.py migrate --run-syncdb 2>nul

REM Tao VN stock bot accounts neu chua co
python manage.py create_bots 2>nul

REM Tao Crypto bot accounts neu chua co
python manage.py create_crypto_bots 2>nul

REM Tao Futures bot accounts neu chua co
python manage.py create_futures_bots 2>nul

cd ..

REM === START BACKEND SERVER ===
echo [2/4] Khoi dong Django backend (port 8000)...
start "StockSim Backend" cmd /k "cd /d %~dp0backend && call venv\Scripts\activate.bat && python manage.py runserver"

REM Cho backend khoi dong
timeout /t 3 /nobreak >nul

REM === START FRONTEND ===
echo [4/4] Khoi dong Frontend (port 3000)...
start "StockSim Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

REM Cho frontend build xong
timeout /t 5 /nobreak >nul

echo.
echo  =====================================================
echo   TAT CA DA CHAY! Mo trinh duyet:
echo   http://localhost:3000
echo.
echo   Bot AI tu dong giao dich sau 60s khoi dong
echo   Bot AI chay them luc 14:30 hang ngay
echo   Xem VN Bot: http://localhost:3000/bots
   Xem CryptoSim: http://localhost:3000/crypto
echo  =====================================================
echo.

REM Mo browser
start http://localhost:3000

pause
