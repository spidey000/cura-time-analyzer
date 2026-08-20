"""Input adapters for plain G-code and FlashForge XGCode (.gx)."""

from __future__ import annotations

import struct
from pathlib import Path

_MAGIC = b"xgcode 1.0\n"


def read_gcode_lines(path: str | Path) -> tuple[list[str], dict[str, int | str]]:
    source = Path(path)
    data = source.read_bytes()
    if data.startswith(_MAGIC):
        return _read_gx(data)
    return data.decode("utf-8", errors="replace").splitlines(), {"format": "gcode"}


def _read_gx(data: bytes) -> tuple[list[str], dict[str, int | str]]:
    if len(data) < 0x20:
        raise ValueError("El archivo GX no contiene una cabecera completa")
    _, gcode_offset, repeated_offset, print_time, filament0, filament1 = struct.unpack_from("<6I", data, 0x10)
    if gcode_offset != repeated_offset:
        raise ValueError("La cabecera GX contiene offsets de G-code inconsistentes")
    if gcode_offset < len(_MAGIC) or gcode_offset >= len(data):
        raise ValueError("El offset de G-code de la cabecera GX no es válido")
    text = data[gcode_offset:].decode("utf-8", errors="replace")
    metadata: dict[str, int | str] = {
        "format": "gx",
        "gcode_offset": gcode_offset,
        "header_time_seconds": print_time,
        "filament0_mm": filament0,
        "filament1_mm": filament1,
    }
    return text.splitlines(), metadata
