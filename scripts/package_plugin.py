#!/usr/bin/env python3
"""Build a Cura .plugin archive from the repository root."""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "dist" / "CuraTimeAnalyzer.plugin"
EXCLUDED = {".git", ".pytest_cache", "dist", "__pycache__", ".venv"}

OUTPUT.parent.mkdir(exist_ok=True)
with ZipFile(OUTPUT, "w", ZIP_DEFLATED) as archive:
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in EXCLUDED for part in path.parts):
            continue
        if path.name.endswith((".pyc", ".gcode")):
            continue
        archive.write(path, path.relative_to(ROOT))
print(OUTPUT)
