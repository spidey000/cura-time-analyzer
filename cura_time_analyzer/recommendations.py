"""Explainable, deterministic recommendations."""

from __future__ import annotations

from .models import AnalysisRun, Evidence, MotionCategory, ParameterCandidate, Recommendation


def build_recommendations(result: AnalysisRun) -> list[Recommendation]:
    if not result.layers or result.total_time_seconds <= 0:
        return []
    recommendations: list[Recommendation] = []
    total = result.total_time_seconds
    travel = result.global_stats.category_times.get(MotionCategory.TRAVEL, 0.0)
    wall = sum(result.global_stats.category_times.get(item, 0.0) for item in (MotionCategory.WALL_OUTER, MotionCategory.WALL_INNER))
    infill = result.global_stats.category_times.get(MotionCategory.INFILL, 0.0)
    support = sum(result.global_stats.category_times.get(item, 0.0) for item in (MotionCategory.SUPPORT, MotionCategory.SUPPORT_INTERFACE))

    def add(identifier: str, explanation: str, seconds: float, keys: list[str], severity: str = "suggestion") -> None:
        recommendations.append(Recommendation(
            id=identifier,
            severity=severity,
            title_key=f"recommendation.{identifier}.title",
            explanation_key=explanation,
            evidence=[Evidence("time_seconds", seconds, "s"), Evidence("share", seconds / total * 100, "%")],
            parameter_candidates=[ParameterCandidate(key, f"setting.{key}") for key in keys],
        ))

    if travel / total >= 0.20:
        add("travel_dominant", "recommendation.travel_dominant.explanation", travel, ["travel_speed", "travel_avoid_distance", "combing_mode"])
    if wall / total >= 0.35:
        add("walls_dominant", "recommendation.walls_dominant.explanation", wall, ["wall_line_count", "outer_wall_speed", "inner_wall_speed"])
    if infill / total >= 0.25:
        add("infill_dominant", "recommendation.infill_dominant.explanation", infill, ["infill_density", "infill_speed", "infill_pattern"])
    if support / total >= 0.20:
        add("support_dominant", "recommendation.support_dominant.explanation", support, ["support_density", "support_speed", "support_pattern"])
    if result.global_stats.retraction_count >= max(5, result.layer_count * 3):
        add("many_retractions", "recommendation.many_retractions.explanation", result.global_stats.category_times.get(MotionCategory.RETRACTION, 0.0), ["retraction_distance", "retraction_speed", "maximum_retraction_count"])
    return recommendations
