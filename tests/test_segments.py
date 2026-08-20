from pathlib import Path

from cura_time_analyzer.analysis import analyze_lines
from cura_time_analyzer.models import MotionCategory


FIXTURE = Path(__file__).parent / "fixtures" / "basic.gcode"


def test_analysis_keeps_toolpath_segments_for_heatmap():
    result = analyze_lines(FIXTURE.read_text().splitlines())

    segments = result.layers[0].segments

    assert segments
    assert all(segment.estimated_time_seconds >= 0 for segment in segments)
    assert any(segment.category == MotionCategory.WALL_OUTER for segment in segments)
    assert segments[0].x_start_mm is not None
    assert segments[0].x_end_mm is not None
