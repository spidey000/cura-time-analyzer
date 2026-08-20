import json
from pathlib import Path

from cura_time_analyzer.controller import AnalysisController


def test_controller_exports_json_and_csv(tmp_path: Path):
    controller = AnalysisController()
    controller.analyze_file(Path(__file__).parent / "fixtures" / "basic.gcode")
    json_path = tmp_path / "analysis.json"
    csv_path = tmp_path / "layers.csv"

    controller.export_json(json_path)
    controller.export_csv(csv_path)

    assert json.loads(json_path.read_text())["layer_count"] == 2
    assert csv_path.read_text().splitlines()[0].startswith("layer,z_height_mm")
