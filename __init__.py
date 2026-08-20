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
        add_menu_item = getattr(self, "addMenuItem", None)
        if not callable(add_menu_item):
            add_menu_item = getattr(self._application, "addMenuItem", None)
        if callable(add_menu_item):
            add_menu_item("Analizar tiempo por capa…", self._open_dialog)

    def _open_dialog(self):
        self._dialog = AnalysisDialog()
        self._dialog.show()
        self._dialog.raise_()
        self._dialog.activateWindow()


def getMetaData():
    # Plugin identity and SDK compatibility live in the mandatory plugin.json.
    return {}


def register(app):
    return {"extension": CuraTimeAnalyzerExtension(app)}
