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

Ao abrir, o app consulta em segundo plano a última release pública de `cvinni21/Universal_Downloader`; se encontrar uma versão nova, pede confirmação antes de baixar e instalar. **Verificar atualizações** também permite consultar manualmente. Salve uma release estável com uma tag de versão maior (por exemplo, `v1.2.0`) e anexe um arquivo chamado exatamente `Universal_Downloader.exe` para publicar uma atualização.

O atualizador só substitui o executável depois de o usuário aceitar. Ao executar a versão Python, o app informa a página da release para baixar manualmente. A versão do app é definida em `updater.py`.

O workflow `.github/workflows/release.yml` compila e publica o app, o host do navegador e a extensão quando uma tag `v*` é enviada ao GitHub. O repositório padrão do atualizador já está configurado como `cvinni21/Universal_Downloader`.

## Recursos

- Qualidade máxima, MP4, original, 1080p, 720p, 480p, MP3 e M4A.
- Playlists, cookies do Chrome, Edge, Firefox, Brave e Opera.
- Download de legendas e inclusão de metadados.
- Nome e pasta de destino personalizáveis.
- Preferências guardadas em `%APPDATA%/UniversalDownloader/settings.json`.
- Política de conexão padrão ou cuidadosa, com pausas e tentativas em espera progressiva para respeitar limites e reduzir erros temporários.

## Integração com o navegador

No Windows, a extensão é opcional. Como este projeto não será publicado na Chrome Web Store, o Chrome exige uma etapa manual: ativar o modo de desenvolvedor e usar **Carregar sem compactação**. O instalador abre a tela e a pasta corretas para deixar isso mais simples.

A extensão em `browser_extension/` oferece um menu de contexto para enviar um link ao app e uma opção de interceptação automática de downloads, desativada por padrão. Para a instalação manual de prévia:

1. Baixe `Universal_Downloader_Portable_Windows.zip` na página de releases e extraia a pasta.
2. Dê dois cliques em `INSTALAR_INTEGRACAO.bat`. Ele instala uma cópia do app e do auxiliar em `%LOCALAPPDATA%/UniversalDownloader`, registra a integração e abre a página de extensões e a pasta da extensão.
3. No Chrome, Edge ou Brave, ative o modo de desenvolvedor, escolha **Carregar sem compactação** e selecione a pasta que o instalador abriu.
4. A interceptação automática fica desligada até ser ativada no ícone da extensão. Também é possível clicar com o botão direito em um link e escolher **Baixar link com Universal Downloader**.

Para uso sem extensão, extraia o ZIP e abra `Universal_Downloader.exe`. O app não precisa de Python instalado.

O Firefox usa `about:debugging#/runtime/this-firefox` para carregar o `manifest.json`. Ao receber um link, o app inicia o download automaticamente; links recebidos enquanto outro download está ativo entram na fila. Use apenas downloads que você tem autorização para salvar.
