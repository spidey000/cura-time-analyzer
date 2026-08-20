"""Explainable what-if estimates for configuration changes.

Speed-only variants are algebraic estimates. Geometry-changing variants must be
re-sliced and are intentionally represented as requiring_reslice=True.
"""

from __future__ import annotations

from dataclasses import dataclass

from .models import AnalysisRun, MotionCategory


@dataclass(frozen=True)
class VariantEstimate:
    parameter_key: str
    baseline_value: float | int | str | None
    proposed_value: float | int | str | None
    estimated_total_seconds: float | None
    estimated_savings_seconds: float | None
    requires_reslice: bool
    explanation: str


_SPEED_CATEGORIES = {
    "outer_wall_speed": (MotionCategory.WALL_OUTER,),
    "inner_wall_speed": (MotionCategory.WALL_INNER,),
    "infill_speed": (MotionCategory.INFILL,),
    "support_speed": (MotionCategory.SUPPORT, MotionCategory.SUPPORT_INTERFACE),
    "travel_speed": (MotionCategory.TRAVEL,),
}

STRUCTURAL_SETTINGS = (
    "wall_line_count",
    "layer_height",
    "infill_density",
    "infill_pattern",
    "support_density",
    "support_pattern",
)


def rank_speed_variants(result: AnalysisRun, profile: dict[str, float], percent_increase: float = 20.0) -> list[VariantEstimate]:
    variants: list[VariantEstimate] = []
    factor = 1.0 + percent_increase / 100.0
    for parameter, categories in _SPEED_CATEGORIES.items():
        baseline = profile.get(parameter)
        if baseline is None or baseline <= 0:
            continue
        category_time = sum(result.global_stats.category_times.get(category, 0.0) for category in categories)
        if category_time <= 0:
            continue
        new_total = result.total_time_seconds - category_time + category_time / factor
        variants.append(VariantEstimate(
            parameter_key=parameter,
            baseline_value=baseline,
            proposed_value=round(baseline * factor, 2),
            estimated_total_seconds=new_total,
            estimated_savings_seconds=result.total_time_seconds - new_total,
            requires_reslice=False,
            explanation="Estimación ideal: solo cambia la velocidad de esta categoría y el firmware puede mantenerla.",
        ))
    return sorted(variants, key=lambda item: item.estimated_savings_seconds or 0.0, reverse=True)


def structural_variants(profile: dict[str, float | int | str | None]) -> list[VariantEstimate]:
    return [VariantEstimate(
        parameter_key=key,
        baseline_value=profile.get(key),
        proposed_value=None,
        estimated_total_seconds=None,
        estimated_savings_seconds=None,
        requires_reslice=True,
        explanation="Este cambio altera la geometría del toolpath; requiere crear una copia y volver a laminar.",
    ) for key in STRUCTURAL_SETTINGS if key in profile]
