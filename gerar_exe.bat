@echo off
setlocal
cd /d "%~dp0"
echo Instalando dependencias e criando o executavel...
python -m pip install -r requirements.txt
if errorlevel 1 goto failed
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0build.ps1"
if errorlevel 1 goto failed
echo.
echo Executavel criado em dist\Universal_Downloader.exe
pause
exit /b 0

:failed
echo.
echo A instalacao ou compilacao falhou. Veja a mensagem acima.
pause
exit /b 1
