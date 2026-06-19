@echo off
cd /d "%~dp0.."

if not exist ".venv\Scripts\python.exe" (
    call :full_setup
    exit /b %errorlevel%
)

call .venv\Scripts\activate.bat

python -c "import typer" >nul 2>&1
if errorlevel 1 (
    echo  Dependencias em falta -- a instalar...
    pip install -q -e .
    pip install -q pytest
)


exit /b 0

:full_setup
echo.
echo  Primeira execucao -- a configurar o ambiente ^(pode demorar alguns minutos^)...
echo.

py -3.14 --version >nul 2>&1
if errorlevel 1 (
    echo  [ERRO] Python 3.14 nao encontrado.
    echo  Descarrega em: https://www.python.org/downloads/
    exit /b 1
)

echo  [1/3] A criar ambiente virtual Python 3.14...
py -3.14 -m venv .venv
if errorlevel 1 (
    echo.
    echo  [ERRO] Falha ao criar o ambiente virtual.
    echo  Se estiveres no PowerShell e der erro de politica, corre primeiro:
    echo    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
    echo.
    exit /b 1
)

call .venv\Scripts\activate.bat

echo  [2/3] A instalar dependencias Python...
pip install -q -e .
pip install -q pytest
if errorlevel 1 (
    echo  [ERRO] pip install falhou.
    exit /b 1
)

echo  [3/3] A instalar Playwright Chromium...
python -m playwright install chromium
if errorlevel 1 (
    echo  [ERRO] playwright install falhou.
    exit /b 1
)

echo.
echo  Setup completo!
echo.
exit /b 0
