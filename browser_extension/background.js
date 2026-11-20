const NATIVE_HOST = "com.universal_downloader.host";
const MENU_LINK = "ud-download-link";
const MENU_PAGE = "ud-download-page";
const MENU_SELECTION = "ud-download-selection";

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.removeAll(() => {
    chrome.contextMenus.create({ id: MENU_LINK, title: "Baixar link com Universal Downloader", contexts: ["link"] });
    chrome.contextMenus.create({ id: MENU_PAGE, title: "Enviar esta página ao Universal Downloader", contexts: ["page"] });
    chrome.contextMenus.create({ id: MENU_SELECTION, title: "Enviar seleção ao Universal Downloader", contexts: ["selection"] });
  });
});

function sendToApp(url) {
  if (!/^https?:\/\//i.test(url || "")) {
    return Promise.reject(new Error("Somente links HTTP ou HTTPS são aceitos."));
  }
  return new Promise((resolve, reject) => {
    let finished = false;
    const port = chrome.runtime.connectNative(NATIVE_HOST);
    const timer = setTimeout(() => finish(new Error("O app não respondeu. Execute o instalador da integração.")), 8000);
    function finish(error, response) {
      if (finished) return;
      finished = true;
      clearTimeout(timer);
      port.disconnect();
      if (error) reject(error);
      else if (!response?.ok) reject(new Error(response?.error || "Não foi possível enviar o link."));
      else resolve(response);
    }
    port.onMessage.addListener(response => finish(null, response));
    port.onDisconnect.addListener(() => {
      if (finished) return;
      const reason = chrome.runtime.lastError?.message || "Integração nativa não encontrada.";
      finish(new Error(reason));
    });
    port.postMessage({ url });
  });
}

async function remember(status) {
  await chrome.storage.local.set({ lastStatus: status, lastStatusAt: Date.now() });
}

chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  const url = info.menuItemId === MENU_LINK ? info.linkUrl
    : info.menuItemId === MENU_SELECTION ? info.selectionText?.trim()
      : tab?.url;
  try {
    await sendToApp(url);
    await remember("Link enviado ao Universal Downloader.");
  } catch (error) {
    await remember(error.message);
  }
});

chrome.downloads.onCreated.addListener(async item => {
  const { autoIntercept = false } = await chrome.storage.local.get({ autoIntercept: false });
  if (!autoIntercept || !/^https?:\/\//i.test(item.url || "") || item.byExtensionId === chrome.runtime.id) return;
  try {
    await sendToApp(item.url);
    chrome.downloads.cancel(item.id, () => {
      chrome.downloads.erase({ id: item.id });
    });
    await remember("Download recebido pelo app.");
  } catch (error) {
    await remember(`Não foi possível interceptar: ${error.message}`);
  }
});

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message?.type === "set-auto-intercept") {
    chrome.storage.local.set({ autoIntercept: Boolean(message.enabled) }, () => sendResponse({ ok: true }));
    return true;
  }
  if (message?.type === "get-status") {
    chrome.storage.local.get({ autoIntercept: false, lastStatus: "Integração pronta." }, sendResponse);
    return true;
  }
});
