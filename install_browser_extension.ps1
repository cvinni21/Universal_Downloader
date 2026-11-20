$ErrorActionPreference = "Stop"
$hostName = "com.universal_downloader.host"
$chromeExtensionId = "lpoijjpgnnmkmkiafiepdneepllnpkoh"
$firefoxExtensionId = "universal-downloader@cvinni21"
$appExe = Join-Path $PSScriptRoot "Universal_Downloader.exe"
$nativeHostExe = Join-Path $PSScriptRoot "Universal_Downloader_NativeHost.exe"
$sourceExtension = Join-Path $PSScriptRoot "browser_extension"
$installRoot = Join-Path $env:LOCALAPPDATA "UniversalDownloader"
$extensionPath = Join-Path $installRoot "browser_extension"
$installedAppExe = Join-Path $installRoot "Universal_Downloader.exe"
$installedNativeHostExe = Join-Path $installRoot "Universal_Downloader_NativeHost.exe"

if (-not (Test-Path -LiteralPath $appExe)) {
    throw "Universal_Downloader.exe precisa estar na mesma pasta deste script."
}
if (-not (Test-Path -LiteralPath $nativeHostExe)) {
    throw "Universal_Downloader_NativeHost.exe precisa estar na mesma pasta deste script."
}
if (-not (Test-Path -LiteralPath $sourceExtension)) {
    throw "A pasta browser_extension não foi encontrada ao lado deste script."
}

New-Item -ItemType Directory -Path $installRoot -Force | Out-Null
New-Item -ItemType Directory -Path $extensionPath -Force | Out-Null
Copy-Item -LiteralPath $appExe -Destination $installedAppExe -Force
Copy-Item -LiteralPath $nativeHostExe -Destination $installedNativeHostExe -Force
Copy-Item -Path (Join-Path $sourceExtension "*") -Destination $extensionPath -Recurse -Force

$chromeManifest = @{
    name = $hostName
    description = "Universal Downloader native messaging host"
    path = [System.IO.Path]::GetFullPath($installedNativeHostExe)
    type = "stdio"
    allowed_origins = @("chrome-extension://$chromeExtensionId/")
}
$firefoxManifest = @{
    name = $hostName
    description = "Universal Downloader native messaging host"
    path = [System.IO.Path]::GetFullPath($installedNativeHostExe)
    type = "stdio"
    allowed_extensions = @($firefoxExtensionId)
}
$chromeManifestPath = Join-Path $installRoot "chrome-host.json"
$firefoxManifestPath = Join-Path $installRoot "firefox-host.json"
$chromeManifest | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $chromeManifestPath -Encoding ascii
$firefoxManifest | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $firefoxManifestPath -Encoding ascii

$registrations = @(
    @{ Key = "Software\Google\Chrome\NativeMessagingHosts\$hostName"; Value = $chromeManifestPath },
    @{ Key = "Software\Microsoft\Edge\NativeMessagingHosts\$hostName"; Value = $chromeManifestPath },
    @{ Key = "Software\BraveSoftware\Brave-Browser\NativeMessagingHosts\$hostName"; Value = $chromeManifestPath },
    @{ Key = "Software\Mozilla\NativeMessagingHosts\$hostName"; Value = $firefoxManifestPath }
)
foreach ($registration in $registrations) {
    $key = [Microsoft.Win32.Registry]::CurrentUser.CreateSubKey($registration.Key)
    $key.SetValue("", $registration.Value, [Microsoft.Win32.RegistryValueKind]::String)
    $key.Close()
}

Write-Host "Integração nativa registrada no perfil atual do Windows."
Write-Host "O app e o auxiliar foram instalados em $installRoot."
Write-Host "Chrome, Edge ou Brave: abra a página de extensões, ative o modo de desenvolvedor e carregue esta pasta:"
Write-Host $extensionPath
Write-Host "Firefox: use about:debugging#/runtime/this-firefox e carregue o manifest.json dessa pasta."

$browserCandidates = @()
foreach ($programFilesRoot in @($env:ProgramFiles, ${env:ProgramFiles(x86)})) {
    if (-not [string]::IsNullOrWhiteSpace($programFilesRoot)) {
        $browserCandidates += @(
            (Join-Path $programFilesRoot "Google\Chrome\Application\chrome.exe"),
            (Join-Path $programFilesRoot "Microsoft\Edge\Application\msedge.exe")
        )
    }
}
if (-not [string]::IsNullOrWhiteSpace($env:LOCALAPPDATA)) {
    $browserCandidates += Join-Path $env:LOCALAPPDATA "BraveSoftware\Brave-Browser\Application\brave.exe"
}
$browserExe = $browserCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if ($browserExe) { Start-Process -FilePath $browserExe -ArgumentList "chrome://extensions/" }
Start-Process -FilePath explorer.exe -ArgumentList "`"$extensionPath`""
Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.MessageBox]::Show(
    "O app e o auxiliar foram instalados. Na página de extensões, ative 'Modo do desenvolvedor' e clique em 'Carregar sem compactação'. Selecione a pasta que acabou de abrir: $extensionPath",
    "Último passo: carregar a extensão",
    [System.Windows.Forms.MessageBoxButtons]::OK,
    [System.Windows.Forms.MessageBoxIcon]::Information
) | Out-Null
