@echo off
cd /d "%~dp0.."
call "%~dp0setup.bat"
if errorlevel 1 exit /b 1
python -m src.cli serve %*
