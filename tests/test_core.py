from pathlib import Path

from cura_time_analyzer.analysis import analyze_lines
from cura_time_analyzer.models import MotionCategory
from cura_time_analyzer.recommendations import build_recommendations


FIXTURES = Path(__file__).parent / "fixtures"


def test_analyze_layers_and_categories():
    result = analyze_lines((FIXTURES / "basic.gcode").read_text().splitlines())

    assert result.layer_count == 2
    assert result.total_time_seconds > 0
    assert result.layers[0].category_times[MotionCategory.WALL_OUTER] > 0
    assert result.layers[0].category_times[MotionCategory.TRAVEL] > 0
    assert result.layers[1].category_times[MotionCategory.INFILL] > 0


def test_parser_tracks_retractions_and_unknown_lines():
    result = analyze_lines((FIXTURES / "retractions.gcode").read_text().splitlines())

    assert result.layers[0].retraction_count == 1
    assert result.layers[0].category_times[MotionCategory.RETRACTION] > 0
    assert result.parser_warnings


def test_recommendations_explain_dominant_travel():
    result = analyze_lines((FIXTURES / "travel_heavy.gcode").read_text().splitlines())

    recommendations = build_recommendations(result)

    assert any("travel" in item.explanation_key for item in recommendations)
    assert any("travel_speed" in candidate.key for item in recommendations for candidate in item.parameter_candidates)


def test_json_shape_is_ready_for_future_comparisons():
    result = analyze_lines((FIXTURES / "basic.gcode").read_text().splitlines())
    payload = result.to_dict()

    assert payload["schema_version"] == "1.0"
    assert payload["analysis_run_id"]
    assert payload["layers"][0]["category_times"]
    assert "comparison" not in payload
