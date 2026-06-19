@echo off
setlocal

cd /d "%~dp0.."

if "%~1"=="" (
    echo.
    echo  Uso: scan.bat ^<URL^> [opcoes]
    echo.
    echo  Exemplos:
    echo    bat\scan.bat https://sapo.pt
    echo    bat\scan.bat https://sapo.pt --quiet
    echo    bat\scan.bat https://sapo.pt --no-history
    echo.
    echo  Resultados guardados automaticamente em docs\data\
    echo.
    exit /b 1
)

call "%~dp0setup.bat"
if errorlevel 1 exit /b 1

python -m src.cli analyze %*
