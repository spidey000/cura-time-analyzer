"""Application service used by Cura UI and future comparison workflows."""

from __future__ import annotations

from pathlib import Path

from .analysis import analyze_lines
from .exporters import write_csv, write_json
from .inputs import read_gcode_lines
from .models import AnalysisRun
from .recommendations import build_recommendations


class AnalysisController:
    def __init__(self) -> None:
        self.last_result: AnalysisRun | None = None
        self.last_source: str | None = None

    def analyze_file(self, path: str | Path) -> AnalysisRun:
        source = Path(path)
        lines, metadata = read_gcode_lines(source)
        result = analyze_lines(lines)
        result.input_metadata = metadata
        result.recommendations = build_recommendations(result)
        self.last_result = result
        self.last_source = str(source)
        return result

    def export_json(self, path: str | Path) -> None:
        write_json(self._require_result(), path)

    def export_csv(self, path: str | Path) -> None:
        write_csv(self._require_result(), path)

    def _require_result(self) -> AnalysisRun:
        if self.last_result is None:
            raise RuntimeError("No hay ningún análisis disponible")
        return self.last_result
