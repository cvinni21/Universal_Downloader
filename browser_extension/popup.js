const toggle = document.getElementById("auto");
const status = document.getElementById("status");

chrome.runtime.sendMessage({ type: "get-status" }, result => {
  if (chrome.runtime.lastError) {
    status.textContent = "Integração nativa não encontrada.";
    return;
  }
  toggle.checked = Boolean(result.autoIntercept);
  status.textContent = result.lastStatus || "Integração pronta.";
});

toggle.addEventListener("change", () => {
  chrome.runtime.sendMessage({ type: "set-auto-intercept", enabled: toggle.checked }, () => {
    if (chrome.runtime.lastError) status.textContent = "Não foi possível salvar a preferência.";
    else status.textContent = toggle.checked ? "Interceptação automática ativada." : "Interceptação automática desativada.";
  });
});
