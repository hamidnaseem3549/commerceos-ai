@echo off
echo 🛑 Stopping CommerceOS AI...

:: Kill processes by port (more precise)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do taskkill /f /pid %%a 2>nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000 ^| findstr LISTENING') do taskkill /f /pid %%a 2>nul

echo ✅ Stopped services on ports 8000 and 3000.
