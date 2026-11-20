@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "%~dp0install_browser_extension.ps1"
if errorlevel 1 (
  echo Nao foi possivel configurar a integracao. Verifique se Universal_Downloader.exe, Universal_Downloader_NativeHost.exe e a pasta browser_extension estao aqui.
  pause
  exit /b 1
)
exit /b 0
