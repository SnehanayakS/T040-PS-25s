@echo off
cd /d "%~dp0"
echo ===================================================
echo RUNNING TEST SUITE (27 TESTS)
echo ===================================================
echo.
python -m unittest discover tests
echo.
pause
