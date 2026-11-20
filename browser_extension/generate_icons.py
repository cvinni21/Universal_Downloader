"""Generate the simple PNG icons used by the browser extension/store listing."""

from __future__ import annotations

import struct
import zlib
from pathlib import Path


ROOT = Path(__file__).parent / "icons"
BLUE = (109, 140, 255, 255)
WHITE = (255, 255, 255, 255)


def chunk(kind: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def make_icon(size: int) -> bytes:
    pixels = [[(0, 0, 0, 0) for _x in range(size)] for _y in range(size)]
    margin = size / 8
    radius = size * 0.2
    left = top = margin
    right = bottom = size - margin - 1
    for y in range(size):
        for x in range(size):
            cx = min(max(x, left + radius), right - radius)
            cy = min(max(y, top + radius), bottom - radius)
            if left <= x <= right and top <= y <= bottom and (x - cx) ** 2 + (y - cy) ** 2 <= radius ** 2:
                pixels[y][x] = BLUE

    center = size / 2
    shaft_half = max(1, round(size * 0.055))
    shaft_top = round(size * 0.25)
    shaft_bottom = round(size * 0.57)
    head_top = round(size * 0.46)
    head_bottom = round(size * 0.77)
    head_half = size * 0.22
    for y in range(shaft_top, shaft_bottom + 1):
        for x in range(round(center) - shaft_half, round(center) + shaft_half + 1):
            pixels[y][x] = WHITE
    for y in range(head_top, head_bottom + 1):
        progress = (y - head_top) / max(1, head_bottom - head_top)
        half = round(head_half * progress)
        for x in range(round(center) - half, round(center) + half + 1):
            pixels[y][x] = WHITE

    rows = b"".join(b"\x00" + bytes(channel for pixel in row for channel in pixel) for row in pixels)
    header = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(rows, 9)) + chunk(b"IEND", b"")


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    for size in (16, 48, 128):
        (ROOT / f"icon{size}.png").write_bytes(make_icon(size))


if __name__ == "__main__":
    main()
