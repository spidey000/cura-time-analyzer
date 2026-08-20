#!/usr/bin/env python3
"""Build a Cura Marketplace-compatible package archive."""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parent.parent
PACKAGE_ID = "CuraTimeAnalyzer"
OUTPUT = ROOT / "dist" / f"{PACKAGE_ID}.plugin"
EXCLUDED_PARTS = {".git", ".github", ".pytest_cache", "__pycache__", "dist"}
EXCLUDED_FILES = {".gitignore", "pyproject.toml"}


def main() -> None:
    OUTPUT.parent.mkdir(exist_ok=True)
    with ZipFile(OUTPUT, "w", ZIP_DEFLATED) as archive:
        for path in sorted(ROOT.rglob("*")):
            if not path.is_file() or any(part in EXCLUDED_PARTS for part in path.parts):
                continue
            if path.name in EXCLUDED_FILES or path.suffix in {".pyc", ".plugin", ".zip"}:
                continue
            relative = path.relative_to(ROOT)
            archive.write(path, f"{PACKAGE_ID}/{relative.as_posix()}")
    print(OUTPUT)


if __name__ == "__main__":
    main()
