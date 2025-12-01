@echo off
echo Stopping any existing Flask servers...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *Flask*" 2>nul
timeout /t 2 /nobreak >nul

echo.
echo Starting Flask dashboard...
echo.
call venv\Scripts\activate.bat
python app.py

