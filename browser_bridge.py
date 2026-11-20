"""Native messaging bridge used by the optional browser extension."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import uuid
from pathlib import Path
from urllib.parse import urlparse


HOST_NAME = "com.universal_downloader.host"
APP_MUTEX = "Local\\UniversalDownloaderDesktop"


def _app_data() -> Path:
    return Path(os.environ.get("APPDATA", Path.home())) / "UniversalDownloader"


def _enqueue(url: str) -> None:
    inbox = _app_data() / "browser_inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    target = inbox / f"{uuid.uuid4().hex}.json"
    temporary = target.with_suffix(".tmp")
    temporary.write_text(json.dumps({"url": url}), encoding="utf-8")
    os.replace(temporary, target)


def drain_browser_inbox() -> list[str]:
    inbox = _app_data() / "browser_inbox"
    if not inbox.exists():
        return []
    urls = []
    for item in sorted(inbox.glob("*.json")):
        try:
            message = json.loads(item.read_text(encoding="utf-8"))
            url = message.get("url", "")
            if urlparse(url).scheme in {"http", "https"}:
                urls.append(url)
            item.unlink(missing_ok=True)
        except (OSError, ValueError, AttributeError):
            continue
    return urls


def claim_single_instance():
    """Return a Windows mutex handle, or None when another UI already owns it."""
    if os.name != "nt":
        return True
    import ctypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    create_mutex = kernel32.CreateMutexW
    create_mutex.argtypes = (ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p)
    create_mutex.restype = ctypes.c_void_p
    kernel32.CloseHandle.argtypes = (ctypes.c_void_p,)
    kernel32.CloseHandle.restype = ctypes.c_bool
    handle = create_mutex(None, False, APP_MUTEX)
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    if ctypes.get_last_error() == 183:  # ERROR_ALREADY_EXISTS
        kernel32.CloseHandle(handle)
        return None
    return handle


def _read_exact(stream, length):
    chunks = []
    remaining = length
    while remaining:
        chunk = stream.read(remaining)
        if not chunk:
            return None
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def _respond(message):
    encoded = json.dumps(message, ensure_ascii=False).encode("utf-8")
    sys.stdout.buffer.write(len(encoded).to_bytes(4, "little") + encoded)
    sys.stdout.buffer.flush()


def _start_app():
    if getattr(sys, "frozen", False):
        folder = Path(sys.executable).parent
        gui_app = folder / "Universal_Downloader.exe"
        command = [str(gui_app)]
    else:
        command = [sys.executable, str(Path(sys.argv[0]).resolve())]
        folder = Path(sys.argv[0]).resolve().parent
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    subprocess.Popen(command, cwd=folder, creationflags=flags, close_fds=True)


def run_native_host():
    """Serve Chrome/Edge/Brave native-messaging JSON frames on stdio."""
    stream = sys.stdin.buffer
    app_started = False
    while True:
        header = _read_exact(stream, 4)
        if header is None:
            return
        size = int.from_bytes(header, "little")
        if size <= 0 or size > 1024 * 1024:
            return
        payload = _read_exact(stream, size)
        if payload is None:
            return
        try:
            message = json.loads(payload.decode("utf-8"))
            url = message.get("url", "")
            parsed = urlparse(url)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                _respond({"ok": False, "error": "Only HTTP and HTTPS URLs are accepted."})
                continue
            _enqueue(url)
            _respond({"ok": True})
            if not app_started:
                _start_app()
                app_started = True
        except Exception as exc:
            _respond({"ok": False, "error": str(exc)[:300]})
