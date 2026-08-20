#!/usr/bin/env python3
"""Build and validate a Cura Marketplace-compatible package archive."""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
import json

ROOT = Path(__file__).resolve().parent.parent
PACKAGE_ID = "CuraTimeAnalyzer"
EXCLUDED_PARTS = {".git", ".github", ".pytest_cache", "__pycache__", "dist", "docs", "tests", "scripts"}
EXCLUDED_FILES = {".gitignore", "pyproject.toml", "MARKETPLACE.md", "AGENTS.md"}
MAX_PACKAGE_BYTES = 50 * 1024 * 1024


def main() -> None:
    manifest = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
    output = ROOT / "dist" / f"{PACKAGE_ID}-{manifest['version']}.plugin"
    required = {"name", "author", "version", "description", "supported_sdk_versions"}
    missing = required.difference(manifest)
    if missing:
        raise SystemExit(f"plugin.json missing required fields: {sorted(missing)}")
    if not isinstance(manifest["supported_sdk_versions"], list) or not manifest["supported_sdk_versions"]:
        raise SystemExit("supported_sdk_versions must be a non-empty list")

    output.parent.mkdir(exist_ok=True)
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        for path in sorted(ROOT.rglob("*")):
            if not path.is_file() or any(part in EXCLUDED_PARTS for part in path.parts):
                continue
            if path.name in EXCLUDED_FILES or path.suffix in {".pyc", ".plugin", ".zip"}:
                continue
            relative = path.relative_to(ROOT)
            archive.write(path, f"{PACKAGE_ID}/{relative.as_posix()}")

    if output.stat().st_size > MAX_PACKAGE_BYTES:
        raise SystemExit(f"package exceeds Marketplace limit: {output.stat().st_size} bytes")
    with ZipFile(output) as archive:
        names = set(archive.namelist())
        required_paths = {f"{PACKAGE_ID}/plugin.json", f"{PACKAGE_ID}/__init__.py", f"{PACKAGE_ID}/LICENSE", f"{PACKAGE_ID}/CHANGELOG.md"}
        missing_paths = required_paths.difference(names)
        if missing_paths:
            raise SystemExit(f"package missing required files: {sorted(missing_paths)}")
        if any(name.startswith(("tests/", "docs/", "scripts/")) for name in names):
            raise SystemExit("development-only files leaked into package")
    print(output)


if __name__ == "__main__":
    main()
