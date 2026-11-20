$ErrorActionPreference = "Stop"
$hostName = "com.universal_downloader.host"
$chromeExtensionId = "lpoijjpgnnmkmkiafiepdneepllnpkoh"
$firefoxExtensionId = "universal-downloader@cvinni21"
$appExe = Join-Path $PSScriptRoot "Universal_Downloader.exe"
$nativeHostExe = Join-Path $PSScriptRoot "Universal_Downloader_NativeHost.exe"
$sourceExtension = Join-Path $PSScriptRoot "browser_extension"
$installRoot = Join-Path $env:LOCALAPPDATA "UniversalDownloader"
$extensionPath = Join-Path $installRoot "browser_extension"
$nativeHostPath = Join-Path $installRoot "native-host"

if (-not (Test-Path -LiteralPath $appExe)) {
    throw "Universal_Downloader.exe precisa estar na mesma pasta deste script."
}
if (-not (Test-Path -LiteralPath $nativeHostExe)) {
    throw "Universal_Downloader_NativeHost.exe precisa estar na mesma pasta deste script."
}
if (-not (Test-Path -LiteralPath $sourceExtension)) {
    throw "A pasta browser_extension não foi encontrada ao lado deste script."
}

New-Item -ItemType Directory -Path $installRoot,$nativeHostPath -Force | Out-Null
Copy-Item -Path (Join-Path $sourceExtension "*") -Destination $extensionPath -Recurse -Force

$chromeManifest = @{
    name = $hostName
    description = "Universal Downloader native messaging host"
    path = [System.IO.Path]::GetFullPath($nativeHostExe)
    type = "stdio"
    allowed_origins = @("chrome-extension://$chromeExtensionId/")
}
$firefoxManifest = @{
    name = $hostName
    description = "Universal Downloader native messaging host"
    path = [System.IO.Path]::GetFullPath($nativeHostExe)
    type = "stdio"
    allowed_extensions = @($firefoxExtensionId)
}
$chromeManifestPath = Join-Path $nativeHostPath "chrome-host.json"
$firefoxManifestPath = Join-Path $nativeHostPath "firefox-host.json"
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
Write-Host "Chrome, Edge ou Brave: abra a página de extensões, ative o modo de desenvolvedor e carregue esta pasta:"
Write-Host $extensionPath
Write-Host "Firefox: use about:debugging#/runtime/this-firefox e carregue o manifest.json dessa pasta."
