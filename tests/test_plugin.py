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


def test_plugin_declares_sdk_8_family():
    metadata = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
    assert metadata["supported_sdk_versions"] == [f"8.{minor}.0" for minor in range(10)]


def test_qt_ui_supports_cura_5_qt6_and_legacy_qt5():
    source = (ROOT / "cura_time_analyzer" / "qt_ui.py").read_text(encoding="utf-8")
    assert "from PyQt6.QtCore" in source
    assert "from PyQt5.QtCore" in source
    assert "_SELECT_ROWS" in source
