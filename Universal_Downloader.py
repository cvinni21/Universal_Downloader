"""Universal Downloader — interface desktop para yt-dlp."""

from __future__ import annotations

import json
import os
import queue
import re
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import yt_dlp

from updater import APP_VERSION, check_release, install_release
from browser_bridge import claim_single_instance, drain_browser_inbox, run_native_host


BG = "#0b1020"
PANEL = "#121a2b"
PANEL_ALT = "#182338"
TEXT = "#edf3ff"
MUTED = "#91a0b9"
ACCENT = "#6d8cff"
GREEN = "#35c995"
RED = "#ff7185"


def config_file() -> Path:
    base = Path(os.environ.get("APPDATA", Path.home())) / "UniversalDownloader"
    base.mkdir(parents=True, exist_ok=True)
    return base / "settings.json"


class UniversalDownloaderApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Universal Downloader")
        self.root.geometry("960x700")
        self.root.minsize(720, 540)
        self.root.configure(bg=BG)
        self.events: queue.Queue = queue.Queue()
        self.downloading = False
        self.browser_queue = []
        self.settings = self.load_settings()
        self.url_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.folder_var = tk.StringVar(value=self.settings.get("folder", str(Path.home() / "Downloads")))
        self.quality_var = tk.StringVar(value="Melhor qualidade · MP4")
        self.browser_var = tk.StringVar(value="Não usar cookies")
        self.connection_var = tk.StringVar(value=self.settings.get("connection_mode", "Padrão · 4 segmentos"))
        self.playlist_var = tk.BooleanVar(value=False)
        self.subtitles_var = tk.BooleanVar(value=False)
        self.metadata_var = tk.BooleanVar(value=True)
        self.github_var = tk.StringVar(value=self.settings.get("github_repo") or "cvinni21/Universal_Downloader")
        self.status_var = tk.StringVar(value="Pronto para baixar")
        self.percent_var = tk.StringVar(value="0%")
        self._style()
        self._build_ui()
        self.root.after(100, self._drain_events)
        self.root.after(500, self._check_browser_inbox)
        self.root.after(1500, self._auto_check_updates)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def load_settings(self):
        try:
            return json.loads(config_file().read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def save_settings(self):
        self.settings.update(folder=self.folder_var.get().strip(), github_repo=self.github_var.get().strip(),
                             connection_mode=self.connection_var.get())
        try:
            config_file().write_text(json.dumps(self.settings, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError:
            pass

    def _style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TCombobox", fieldbackground=PANEL_ALT, background=PANEL_ALT, foreground=TEXT,
                        arrowcolor=TEXT, bordercolor=PANEL_ALT, padding=9)
        style.map("TCombobox", fieldbackground=[("readonly", PANEL_ALT)], foreground=[("readonly", TEXT)])
        style.configure("Horizontal.TProgressbar", troughcolor=PANEL_ALT, background=ACCENT, bordercolor=PANEL_ALT,
                        lightcolor=ACCENT, darkcolor=ACCENT, thickness=9)

    def _build_ui(self):
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        outer = tk.Frame(self.root, bg=BG)
        outer.grid(row=0, column=0, sticky="nsew", padx=26, pady=(16, 12))
        outer.grid_columnconfigure(0, weight=1)
        outer.grid_rowconfigure(1, weight=1)

        header = tk.Frame(outer, bg=BG)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        mark = tk.Label(header, text="↓", font=("Segoe UI", 22, "bold"), bg=ACCENT, fg="white", width=3, height=1)
        mark.pack(side="left", padx=(0, 14))
        titles = tk.Frame(header, bg=BG)
        titles.pack(side="left", anchor="w")
        tk.Label(titles, text="Universal Downloader", font=("Segoe UI", 22, "bold"), bg=BG, fg=TEXT).pack(anchor="w")
        tk.Label(titles, text="Vídeos, áudio e playlists em um só lugar", font=("Segoe UI", 10), bg=BG, fg=MUTED).pack(anchor="w", pady=(2, 0))
        tk.Label(header, text=f"v{APP_VERSION}", font=("Segoe UI", 9), bg=PANEL_ALT, fg=MUTED, padx=11, pady=6).pack(side="right", anchor="n")

        content = tk.Frame(outer, bg=BG)
        content.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
        content.grid_rowconfigure(0, weight=1)
        content.grid_columnconfigure(0, weight=1)
        canvas = tk.Canvas(content, bg=BG, highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(content, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns", padx=(8, 0))
        body = tk.Frame(canvas, bg=BG)
        body_window = canvas.create_window((0, 0), window=body, anchor="nw")
        body.bind("<Configure>", lambda _event: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda event: canvas.itemconfigure(body_window, width=event.width))
        self.root.bind_all("<MouseWheel>", lambda event: canvas.yview_scroll(int(-event.delta / 120), "units"))

        card = self._card(body)
        card.pack(fill="x", pady=(0, 14))
        self._label(card, "LINK DO CONTEÚDO")
        row = tk.Frame(card, bg=PANEL)
        row.pack(fill="x", pady=(7, 0))
        self.url_entry = self._entry(row, self.url_var, "Cole aqui o link do vídeo, áudio ou playlist")
        self.url_entry.pack(side="left", fill="x", expand=True, ipady=10)
        self._button(row, "Colar", self._paste, subtle=True).pack(side="left", padx=(9, 0))

        card = self._card(body)
        card.pack(fill="x", pady=(0, 14))
        self._label(card, "SALVAR COMO")
        name_row = tk.Frame(card, bg=PANEL)
        name_row.pack(fill="x", pady=(7, 14))
        self._entry(name_row, self.name_var, "Nome original do conteúdo").pack(fill="x", ipady=9)
        self._label(card, "PASTA DE DESTINO")
        folder_row = tk.Frame(card, bg=PANEL)
        folder_row.pack(fill="x", pady=(7, 0))
        self._entry(folder_row, self.folder_var).pack(side="left", fill="x", expand=True, ipady=9)
        self._button(folder_row, "Escolher pasta", self._choose_folder, subtle=True).pack(side="left", padx=(9, 0))

        options = tk.Frame(body, bg=BG)
        options.pack(fill="x", pady=(0, 14))
        quality_card = self._card(options)
        quality_card.pack(side="left", fill="both", expand=True, padx=(0, 7))
        self._label(quality_card, "FORMATO E QUALIDADE")
        ttk.Combobox(quality_card, textvariable=self.quality_var, state="readonly", values=[
            "Melhor qualidade · MP4", "Melhor qualidade · Original", "1080p · Full HD", "720p · HD",
            "480p · SD", "Somente áudio · MP3", "Somente áudio · M4A original",
        ]).pack(fill="x", pady=(8, 0))
        cookie_card = self._card(options)
        cookie_card.pack(side="left", fill="both", expand=True, padx=(7, 0))
        self._label(cookie_card, "LOGIN DO NAVEGADOR")
        ttk.Combobox(cookie_card, textvariable=self.browser_var, state="readonly", values=[
            "Não usar cookies", "Chrome", "Edge", "Firefox", "Brave", "Opera",
        ]).pack(fill="x", pady=(8, 0))

        connection_card = self._card(body)
        connection_card.pack(fill="x", pady=(0, 14))
        self._label(connection_card, "POLÍTICA DE CONEXÃO")
        ttk.Combobox(connection_card, textvariable=self.connection_var, state="readonly", values=[
            "Padrão · 4 segmentos", "Cuidadoso · pausas entre requisições",
        ]).pack(fill="x", pady=(8, 0))

        extras = self._card(body)
        extras.pack(fill="x", pady=(0, 14))
        self._label(extras, "OPÇÕES")
        checks = tk.Frame(extras, bg=PANEL)
        checks.pack(fill="x", pady=(8, 0))
        self._check(checks, "Baixar playlist inteira", self.playlist_var).pack(side="left", padx=(0, 22))
        self._check(checks, "Incluir legendas disponíveis", self.subtitles_var).pack(side="left", padx=(0, 22))
        self._check(checks, "Adicionar metadados", self.metadata_var).pack(side="left")

        footer = tk.Frame(outer, bg=PANEL, padx=16, pady=10, highlightthickness=1, highlightbackground="#1f2b40")
        footer.grid(row=2, column=0, sticky="ew")
        status_line = tk.Frame(footer, bg=PANEL)
        status_line.pack(fill="x")
        tk.Label(status_line, textvariable=self.status_var, font=("Segoe UI", 9), bg=PANEL, fg=TEXT, anchor="w").pack(side="left", fill="x", expand=True)
        tk.Label(status_line, textvariable=self.percent_var, font=("Segoe UI", 9, "bold"), bg=PANEL, fg=ACCENT).pack(side="right")
        self.progress = ttk.Progressbar(footer, maximum=100)
        self.progress.pack(fill="x", pady=(7, 9))
        actions = tk.Frame(footer, bg=PANEL)
        actions.pack(fill="x")
        self.download_button = self._button(actions, "↓   Iniciar download", self._start_download, primary=True)
        self.download_button.pack(side="left", ipadx=14, ipady=6)
        self._button(actions, "Verificar atualizações", self._check_updates, subtle=True).pack(side="right", ipadx=8, ipady=4)

    def _card(self, parent):
        return tk.Frame(parent, bg=PANEL, padx=18, pady=15, highlightthickness=1, highlightbackground="#1f2b40")

    def _label(self, parent, text):
        tk.Label(parent, text=text, font=("Segoe UI", 8, "bold"), bg=PANEL, fg=MUTED).pack(anchor="w")

    def _entry(self, parent, variable, placeholder=None):
        entry = tk.Entry(parent, textvariable=variable, font=("Segoe UI", 10), bg=PANEL_ALT, fg=TEXT,
                         insertbackground=TEXT, relief="flat", highlightthickness=1, highlightbackground=PANEL_ALT,
                         highlightcolor=ACCENT, bd=0)
        if placeholder and not variable.get():
            entry.insert(0, placeholder)
            entry.configure(fg="#65748c")
            entry.bind("<FocusIn>", lambda _e, w=entry, p=placeholder: self._clear_placeholder(w, p))
            entry.bind("<FocusOut>", lambda _e, w=entry, v=variable, p=placeholder: self._restore_placeholder(w, v, p))
        return entry

    @staticmethod
    def _clear_placeholder(entry, placeholder):
        if entry.get() == placeholder:
            entry.delete(0, "end")
            entry.configure(fg=TEXT)

    @staticmethod
    def _restore_placeholder(entry, variable, placeholder):
        if not variable.get():
            entry.insert(0, placeholder)
            entry.configure(fg="#65748c")

    def _button(self, parent, text, command, primary=False, subtle=False):
        bg = ACCENT if primary else (PANEL_ALT if subtle else "#26334a")
        return tk.Button(parent, text=text, command=command, font=("Segoe UI", 10, "bold" if primary else "normal"),
                         bg=bg, fg="white" if primary else TEXT, activebackground="#5576f0" if primary else "#24334b",
                         activeforeground="white", relief="flat", bd=0, cursor="hand2", padx=13, pady=8)

    def _check(self, parent, text, variable):
        return tk.Checkbutton(parent, text=text, variable=variable, bg=PANEL, fg=TEXT, activebackground=PANEL,
                              activeforeground=TEXT, selectcolor=PANEL_ALT, font=("Segoe UI", 9), cursor="hand2")

    def _paste(self):
        try:
            self.url_var.set(self.root.clipboard_get().strip())
        except tk.TclError:
            pass

    def _choose_folder(self):
        folder = filedialog.askdirectory(initialdir=self.folder_var.get())
        if folder:
            self.folder_var.set(folder)
            self.save_settings()

    def _options(self, folder):
        name = self.name_var.get().strip()
        name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip(" .")
        template = os.path.join(folder, f"{name}.%(ext)s" if name and not self.playlist_var.get() else "%(title)s.%(ext)s")
        opts = {
            "outtmpl": template,
            "noplaylist": not self.playlist_var.get(),
            "ignoreerrors": False,
            "concurrent_fragment_downloads": 4,
            "retries": 10,
            "fragment_retries": 10,
            "progress_hooks": [self._progress_hook],
            "logger": _YtLogger(self.events),
            "quiet": True,
            "no_warnings": True,
        }
        if self.connection_var.get().startswith("Cuidadoso"):
            opts.update(
                concurrent_fragment_downloads=1,
                sleep_interval_requests=1,
                retry_sleep_functions={
                    "http": lambda attempt: min(2 ** attempt, 60),
                    "fragment": lambda attempt: min(2 ** attempt, 60),
                },
            )
        browser = self.browser_var.get().lower()
        if browser != "não usar cookies":
            opts["cookiesfrombrowser"] = (browser,)
        bundled_ffmpeg = Path(getattr(sys, "_MEIPASS", "")) / "ffmpeg.exe"
        if bundled_ffmpeg.is_file():
            opts["ffmpeg_location"] = str(bundled_ffmpeg.parent)
        q = self.quality_var.get()
        if q == "Melhor qualidade · MP4":
            opts.update(format="bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best", merge_output_format="mp4")
        elif q == "Melhor qualidade · Original":
            opts["format"] = "bestvideo+bestaudio/best"
        elif q.startswith("1080p") or q.startswith("720p") or q.startswith("480p"):
            height = {"1080p": 1080, "720p": 720, "480p": 480}[q.split()[0]]
            opts.update(format=f"bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/best[height<={height}]/best", merge_output_format="mp4")
        elif q == "Somente áudio · MP3":
            opts.update(format="bestaudio/best", postprocessors=[{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}])
        else:
            opts["format"] = "bestaudio[ext=m4a]/bestaudio/best"
        if self.subtitles_var.get():
            opts.update(writesubtitles=True, writeautomaticsub=True, subtitlesformat="srt/best", subtitleslangs=["pt", "pt-BR", "en"])
        if self.metadata_var.get():
            opts["postprocessors"] = opts.get("postprocessors", []) + [{"key": "FFmpegMetadata"}]
        return opts

    def _progress_hook(self, data):
        if data["status"] == "downloading":
            total = data.get("total_bytes") or data.get("total_bytes_estimate")
            pct = (data.get("downloaded_bytes", 0) / total * 100) if total else 0
            self.events.put(("progress", pct, f"Baixando · {data.get('_speed_str', '').strip()} · restante {data.get('_eta_str', '').strip()}"))
        elif data["status"] == "finished":
            self.events.put(("progress", 100, "Processando arquivo…"))

    def _start_download(self):
        url = self.url_var.get().strip()
        folder = self.folder_var.get().strip()
        if url == "Cole aqui o link do vídeo, áudio ou playlist":
            url = ""
        if not url:
            messagebox.showwarning("Link necessário", "Cole o link do conteúdo que deseja baixar.", parent=self.root)
            return
        if not os.path.isdir(folder):
            messagebox.showwarning("Pasta inválida", "Escolha uma pasta de destino existente.", parent=self.root)
            return
        if self.downloading:
            return
        self.save_settings()
        self.downloading = True
        self.download_button.configure(state="disabled", text="Baixando…")
        self.progress["value"] = 0
        self.percent_var.set("0%")
        self.status_var.set("Analisando link…")
        threading.Thread(target=self._download_worker, args=(url, folder), daemon=True).start()

    def _check_browser_inbox(self):
        incoming = drain_browser_inbox()
        if incoming:
            if self.downloading:
                self.browser_queue.extend(incoming)
            else:
                self.url_var.set(incoming[0])
                self.browser_queue.extend(incoming[1:])
                self._start_download()
        self.root.after(500, self._check_browser_inbox)

    def _download_worker(self, url, folder):
        try:
            with yt_dlp.YoutubeDL(self._options(folder)) as ydl:
                code = ydl.download([url])
            if code:
                raise RuntimeError("O yt-dlp não conseguiu concluir o download.")
            self.events.put(("done", None, "Download concluído"))
        except Exception as exc:
            self.events.put(("error", str(exc), "Falha no download"))

    def _drain_events(self):
        try:
            while True:
                kind, value, detail = self.events.get_nowait()
                if kind == "progress":
                    self.progress["value"] = value
                    self.percent_var.set(f"{value:.0f}%")
                    self.status_var.set(detail)
                elif kind == "update":
                    if value is None:
                        self.status_var.set("Você já está na versão mais recente")
                        if not detail:
                            messagebox.showinfo("Atualizado", f"Você está usando a versão {APP_VERSION}.", parent=self.root)
                    else:
                        self.status_var.set(f"Atualização {value['version']} disponível")
                        asset = next((a for a in value.get("assets", []) if a["name"].lower() == "universal_downloader.exe"), None)
                        if asset and getattr(sys, "frozen", False):
                            if messagebox.askyesno("Atualização disponível", f"Versão {value['version']} disponível.\n\nDeseja baixar e instalar agora?", parent=self.root):
                                self.status_var.set("Baixando atualização…")
                                threading.Thread(target=install_release, args=(asset["url"], self.root, self.events), daemon=True).start()
                        else:
                            messagebox.showinfo("Atualização disponível", f"Versão {value['version']} disponível.\n\nBaixe o executável em:\n{value.get('url', '')}", parent=self.root)
                elif kind == "install_ready":
                    self.status_var.set("Atualização pronta. Reiniciando…")
                    self.root.after(400, lambda: _restart_with_update(self.root, value))
                elif kind == "update_error":
                    self.status_var.set("Verificação automática indisponível" if detail else "Falha ao atualizar")
                    if not detail:
                        messagebox.showerror("Atualização", value, parent=self.root)
                elif kind == "log":
                    self.status_var.set(f"{detail}: {value[:130]}")
                elif kind in ("done", "error"):
                    self.downloading = False
                    self.download_button.configure(state="normal", text="↓   Iniciar download")
                    self.progress["value"] = 100 if kind == "done" else 0
                    self.percent_var.set("100%" if kind == "done" else "0%")
                    self.status_var.set(detail)
                    if kind == "done":
                        messagebox.showinfo("Tudo pronto", f"Download salvo em:\n{self.folder_var.get()}", parent=self.root)
                    else:
                        messagebox.showerror("Não foi possível baixar", value, parent=self.root)
                    if self.browser_queue:
                        next_url = self.browser_queue.pop(0)
                        self.root.after(300, lambda url=next_url: self._start_queued_browser_download(url))
        except queue.Empty:
            pass
        self.root.after(100, self._drain_events)

    def _check_updates(self):
        repo = self.github_var.get().strip()
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
            repo = self._repo_dialog()
            if not repo:
                return
        self.settings["github_repo"] = repo
        self.save_settings()
        self.status_var.set("Verificando atualizações no GitHub…")
        threading.Thread(target=self._update_worker, args=(repo, False), daemon=True).start()

    def _auto_check_updates(self):
        repo = self.github_var.get().strip()
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
            return
        self.status_var.set("Verificando atualizações…")
        threading.Thread(target=self._update_worker, args=(repo, True), daemon=True).start()

    def _repo_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Repositório de atualizações")
        dialog.configure(bg=PANEL)
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        tk.Label(dialog, text="Informe o repositório GitHub", font=("Segoe UI", 12, "bold"), bg=PANEL, fg=TEXT).pack(anchor="w", padx=20, pady=(18, 4))
        tk.Label(dialog, text="Formato: usuario/repositorio", font=("Segoe UI", 9), bg=PANEL, fg=MUTED).pack(anchor="w", padx=20)
        value = tk.StringVar(value=self.github_var.get())
        ent = tk.Entry(dialog, textvariable=value, bg=PANEL_ALT, fg=TEXT, insertbackground=TEXT, relief="flat", font=("Segoe UI", 10), width=38)
        ent.pack(padx=20, pady=12, ipady=8)
        result = {"repo": None}
        def accept():
            candidate = value.get().strip()
            if re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", candidate):
                result["repo"] = candidate
                self.github_var.set(candidate)
                dialog.destroy()
            else:
                messagebox.showwarning("Formato inválido", "Use usuario/repositorio.", parent=dialog)
        self._button(dialog, "Salvar e verificar", accept, primary=True).pack(padx=20, pady=(0, 18), anchor="e")
        ent.focus_set()
        self.root.wait_window(dialog)
        return result["repo"]

    def _update_worker(self, repo, silent=False):
        try:
            release = check_release(repo, APP_VERSION)
            self.events.put(("update", release, silent))
        except Exception as exc:
            self.events.put(("update_error", str(exc), silent))

    def _on_close(self):
        self.save_settings()
        self.root.destroy()

    def _start_queued_browser_download(self, url):
        self.url_var.set(url)
        self._start_download()


class _YtLogger:
    def __init__(self, events):
        self.events = events
    def debug(self, _msg):
        pass
    def warning(self, msg):
        self.events.put(("log", msg, "Aviso"))
    def error(self, msg):
        self.events.put(("log", msg, "Erro"))


def main():
    if "--native-host" in sys.argv:
        run_native_host()
        return
    instance_handle = claim_single_instance()
    if instance_handle is None:
        return
    root = tk.Tk()
    UniversalDownloaderApp(root)
    root.mainloop()


def _restart_with_update(root, new_exe):
    if getattr(sys, "frozen", False):
        import subprocess
        import tempfile
        current = Path(sys.executable)
        script = Path(tempfile.gettempdir()) / "universal_downloader_update.cmd"
        script.write_text(f'@echo off\r\n:wait\r\ntimeout /t 1 /nobreak >nul\r\ncopy /y "{new_exe}" "{current}" >nul\r\nif errorlevel 1 goto wait\r\nstart "" "{current}"\r\ndel "{new_exe}"\r\ndel "%~f0"\r\n', encoding="utf-8")
        subprocess.Popen(["cmd.exe", "/c", str(script)], creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        root.destroy()
    else:
        messagebox.showinfo("Atualização baixada", f"Executável atualizado salvo em:\n{new_exe}\n\nSubstitua a versão instalada manualmente.", parent=root)


if __name__ == "__main__":
    main()
