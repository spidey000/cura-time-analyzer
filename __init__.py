from __future__ import annotations

try:
    from UM.Extension import Extension
except ImportError:  # pragma: no cover - loaded by Cura
    class Extension:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs):
            pass

try:
    from .qt_ui import AnalysisDialog
except ImportError:  # pytest imports the repository root as a standalone module
    from cura_time_analyzer.qt_ui import AnalysisDialog


class CuraTimeAnalyzerExtension(Extension):
    """Cura menu integration; domain logic remains outside this class."""

    def __init__(self, application):
        super().__init__()
        self._application = application
        self._dialog = None
        self._register_menu()

    def _register_menu(self):
        add_menu_item = getattr(self._application, "addMenuItem", None)
        if add_menu_item:
            add_menu_item("Analizar tiempo por capa…", self._open_dialog)

    def _open_dialog(self):
        self._dialog = AnalysisDialog()
        self._dialog.show()
        self._dialog.raise_()
        self._dialog.activateWindow()


def getMetaData():
    return {
        "plugin": {
            "name": "Cura Time Analyzer",
            "author": "Jorge Martín",
            "version": "0.1.0",
            "description": "Analiza el tiempo estimado por capa y categoría de movimiento.",
            "supported_sdk_versions": ["6.5.0"],
        },
        "extension": {
            "name": "Cura Time Analyzer",
        },
    }


def register(app):
    return {"extension": CuraTimeAnalyzerExtension(app)}
