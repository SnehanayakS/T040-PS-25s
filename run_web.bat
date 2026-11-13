@echo off
cd /d "%~dp0"
echo =====================================================================
echo STARTING ICEGATE CUSTOMS DUTY ASSESSMENT ENGINE (WEB APPLICATION)
echo =====================================================================
echo.
echo Opening Web Portal at http://127.0.0.1:5000 ...
start http://127.0.0.1:5000
echo.
python app.py
pause
