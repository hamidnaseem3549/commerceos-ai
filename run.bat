@echo off
title CommerceOS AI

echo 🚀 Starting CommerceOS AI...
echo.

:: Start Backend
echo 📡 Starting Backend API on port 8000...
start "CommerceOS Backend" cmd /c "cd /d %~dp0 && venv\Scripts\activate && uvicorn backend.main:app --reload --port 8000"

:: Wait a moment for backend to initialize
timeout /t 3 /nobreak >nul

:: Start Frontend
echo 🖥️  Starting Frontend on port 3000...
start "CommerceOS Frontend" cmd /c "cd /d %~dp0frontend && npm run dev"

:: Open browser
timeout /t 5 /nobreak >nul
echo 🌐 Opening http://localhost:3000 ...
start http://localhost:3000

echo.
echo ✅ All services starting! Close this window to stop.
echo    Backend:  http://localhost:8000
echo    Frontend: http://localhost:3000
echo    API Docs: http://localhost:8000/docs
