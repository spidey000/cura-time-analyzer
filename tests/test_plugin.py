import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_plugin_metadata_contract():
    spec = importlib.util.spec_from_file_location("cura_time_analyzer_plugin", ROOT / "__init__.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert module.getMetaData() == {}
    assert "extension" in module.register(None)


def test_plugin_declares_latest_sdk_8_12():
    metadata = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
    assert metadata["supported_sdk_versions"] == ["8.12.0"]


def test_qt_ui_targets_cura_5_qt6():
    source = (ROOT / "cura_time_analyzer" / "qt_ui.py").read_text(encoding="utf-8")
    assert "from PyQt6.QtCore" in source
    assert "PyQt5" not in source
    assert "_SELECT_ROWS" in source
