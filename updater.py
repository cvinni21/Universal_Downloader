"""Small GitHub Releases updater for packaged Windows builds."""

from __future__ import annotations

import json
import re
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

APP_VERSION = "1.1.0"
API = "https://api.github.com/repos/{repo}/releases/latest"


def _version(value):
    parts = re.findall(r"\d+", value or "")
    return tuple(int(p) for p in parts[:4]) if parts else (0,)


def check_release(repo: str, current_version: str):
    request = urllib.request.Request(API.format(repo=repo), headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "Universal-Downloader",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            release = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise ValueError("Não encontrei uma release pública nesse repositório GitHub.") from exc
        raise ValueError(f"GitHub respondeu com erro HTTP {exc.code}.") from exc
    tag = release.get("tag_name", "")
    version = tag.lstrip("vV")
    if release.get("draft") or release.get("prerelease") or _version(version) <= _version(current_version):
        return None
    return {
        "version": version,
        "url": release.get("html_url", ""),
        "assets": [{"name": asset["name"], "url": asset["url"], "browser_url": asset["browser_download_url"]}
                   for asset in release.get("assets", [])],
    }


def install_release(asset_api_url: str, root, events):
    """Download the release executable to a temp file; UI coordinates replacement."""
    try:
        request = urllib.request.Request(asset_api_url, headers={
            "Accept": "application/octet-stream", "User-Agent": "Universal-Downloader",
        })
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = response.read()
        if not payload.startswith(b"MZ"):
            raise ValueError("O arquivo publicado não parece ser um executável Windows válido.")
        destination = Path(tempfile.gettempdir()) / "Universal_Downloader_update.exe"
        destination.write_bytes(payload)
        events.put(("install_ready", str(destination), "Atualização pronta"))
    except Exception as exc:
        events.put(("update_error", str(exc), "Falha na atualização"))
