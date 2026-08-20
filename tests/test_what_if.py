from pathlib import Path

from cura_time_analyzer.analysis import analyze_lines
from cura_time_analyzer.what_if import rank_speed_variants


FIXTURE = Path(__file__).parent / "fixtures" / "basic.gcode"


def test_speed_variants_rank_savings_without_mutating_analysis():
    result = analyze_lines(FIXTURE.read_text().splitlines())
    baseline = {"outer_wall_speed": 35.0, "inner_wall_speed": 50.0}

    variants = rank_speed_variants(result, baseline, percent_increase=20)

    assert variants
    assert variants[0].estimated_savings_seconds >= 0
    assert variants[0].requires_reslice is False
    assert baseline == {"outer_wall_speed": 35.0, "inner_wall_speed": 50.0}
