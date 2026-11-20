# Universal Downloader

Aplicativo Windows para baixar vídeos, áudio e playlists com `yt-dlp`. A interface usa Tkinter, incluído no Python, para manter a instalação pequena e simples.

## Instalar e executar

1. Instale Python 3.10 ou mais recente.
2. Dê dois cliques em `gerar_exe.bat`.
3. Quando terminar, abra `dist/Universal_Downloader.exe`. O segundo arquivo, `dist/Universal_Downloader_NativeHost.exe`, é o auxiliar da extensão de navegador.

Para executar diretamente durante o desenvolvimento:

```powershell
py -3 -m pip install -r requirements.txt
py -3 Universal_Downloader.py
```

Para manter o executável compacto, FFmpeg não é embutido por padrão. Downloads que precisam unir faixas, converter áudio ou criar MP3 precisam de FFmpeg instalado e disponível no PATH. Para gerar um pacote autocontido, compile com `powershell -ExecutionPolicy Bypass -File .\build.ps1 -IncludeFfmpeg` (o executável final fica maior).

## Atualizações pelo GitHub

O botão **Verificar atualizações** consulta a última release pública do repositório configurado. Na primeira utilização, informe o repositório no formato `usuario/repositorio`. Salve uma release estável com a tag de versão (por exemplo, `v1.1.0`) e anexe um arquivo chamado exatamente `Universal_Downloader.exe` para habilitar o download e a substituição automáticos no aplicativo compilado.

O atualizador só substitui o executável depois de o usuário aceitar. Ao executar a versão Python, o app informa a página da release para baixar manualmente. A versão do app é definida em `updater.py`.

O workflow `.github/workflows/release.yml` compila e publica automaticamente o executável quando uma tag `v*` é enviada ao GitHub. Depois de criar um repositório público e enviar o projeto, publique uma tag como `v1.1.0`; informe `usuario/repositorio` no app para receber releases futuras.

## Recursos

- Qualidade máxima, MP4, original, 1080p, 720p, 480p, MP3 e M4A.
- Playlists, cookies do Chrome, Edge, Firefox, Brave e Opera.
- Download de legendas e inclusão de metadados.
- Nome e pasta de destino personalizáveis.
- Preferências guardadas em `%APPDATA%/UniversalDownloader/settings.json`.
- Política de conexão padrão ou cuidadosa, com pausas e tentativas em espera progressiva para respeitar limites e reduzir erros temporários.

## Integração com o navegador

A extensão em `browser_extension/` oferece um menu de contexto para enviar um link ao app e uma opção de interceptação automática de downloads, desativada por padrão. Para instalar:

1. Extraia o Universal Downloader e mantenha `Universal_Downloader.exe`, `Universal_Downloader_NativeHost.exe`, `install_browser_extension.ps1` e a pasta `browser_extension` juntos.
2. Execute `install_browser_extension.ps1` no PowerShell do Windows. Ele registra a comunicação nativa no perfil atual e copia a extensão para `%LOCALAPPDATA%/UniversalDownloader/browser_extension`.
3. No Chrome, Edge ou Brave, abra a página de extensões, ative o modo de desenvolvedor e escolha **Carregar sem compactação** usando a pasta exibida pelo instalador.
4. Abra o ícone da extensão para ativar a interceptação automática se desejar. Também é possível clicar com o botão direito em um link e escolher **Baixar link com Universal Downloader**.

O Firefox usa `about:debugging#/runtime/this-firefox` para carregar o `manifest.json`. Ao receber um link, o app inicia o download automaticamente; links recebidos enquanto outro download está ativo entram na fila. Use apenas downloads que você tem autorização para salvar.
