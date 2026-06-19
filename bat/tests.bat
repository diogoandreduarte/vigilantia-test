@echo off
cd /d "%~dp0.."

call "%~dp0setup.bat"
if errorlevel 1 exit /b 1

echo.
echo  A correr testes...
echo.
python -m pytest tests/ -v %*
