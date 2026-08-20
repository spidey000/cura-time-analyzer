from pathlib import Path

from cura_time_analyzer.analysis import analyze_lines
from cura_time_analyzer.heatmap import HeatmapMode, build_heatmap


FIXTURE = Path(__file__).parent / "fixtures" / "basic.gcode"


def test_heatmap_returns_normalized_colored_segments():
    result = analyze_lines(FIXTURE.read_text().splitlines())

    points = build_heatmap(result, HeatmapMode.TIME, layer_index=0)

    assert points
    assert all(0.0 <= point.intensity <= 1.0 for point in points)
    assert all(len(point.color_rgba) == 4 for point in points)
    assert all(point.layer_index == 0 for point in points)


def test_heatmap_travel_mode_uses_travel_time():
    result = analyze_lines(FIXTURE.read_text().splitlines())

    points = build_heatmap(result, HeatmapMode.TRAVEL, layer_index=0)

    assert any(point.intensity > 0 for point in points if point.category.value == "travel")
