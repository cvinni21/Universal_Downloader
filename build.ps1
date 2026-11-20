param([switch]$IncludeFfmpeg)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCommand) { throw "Python nao encontrado. Instale Python 3 e execute gerar_exe.bat novamente." }

$buildArgs = @(
    "--noconfirm", "--clean", "--onefile", "--windowed",
    "--name", "Universal_Downloader", "--collect-all", "yt_dlp"
)

if ($IncludeFfmpeg) {
    $ffmpeg = Get-Command ffmpeg.exe -ErrorAction SilentlyContinue
    $ffprobe = Get-Command ffprobe.exe -ErrorAction SilentlyContinue
    if (-not $ffmpeg) { throw "FFmpeg nao foi encontrado no PATH." }
    $buildArgs += @("--add-binary", "$($ffmpeg.Source);.")
    if ($ffprobe) { $buildArgs += @("--add-binary", "$($ffprobe.Source);.") }
} else {
    Write-Host "FFmpeg nao sera embutido; MP3 e combinacao de faixas usam FFmpeg instalado no sistema. Use -IncludeFfmpeg para inclui-lo."
}

$buildArgs += "Universal_Downloader.py"
& $pythonCommand.Source -m PyInstaller @buildArgs
if ($LASTEXITCODE -ne 0) { throw "PyInstaller encerrou com codigo $LASTEXITCODE" }

$nativeArgs = @(
    "--noconfirm", "--clean", "--onefile", "--console",
    "--name", "Universal_Downloader_NativeHost", "browser_native_entry.py"
)
& $pythonCommand.Source -m PyInstaller @nativeArgs
if ($LASTEXITCODE -ne 0) { throw "Compilacao do host do navegador encerrou com codigo $LASTEXITCODE" }
