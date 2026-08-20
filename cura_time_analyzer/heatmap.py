"""Heatmap projection data, independent from Cura's renderer."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .models import AnalysisRun, MotionCategory


class HeatmapMode(str, Enum):
    TIME = "time"
    TRAVEL = "travel"
    RETRACTION = "retraction"
    CATEGORY = "category"


@dataclass(frozen=True)
class HeatmapPoint:
    layer_index: int
    x_start_mm: float
    y_start_mm: float
    z_start_mm: float
    x_end_mm: float
    y_end_mm: float
    z_end_mm: float
    category: MotionCategory
    estimated_time_seconds: float
    intensity: float
    color_rgba: tuple[int, int, int, int]


_CATEGORY_COLORS = {
    MotionCategory.WALL_OUTER: (230, 57, 70, 255),
    MotionCategory.WALL_INNER: (245, 130, 31, 255),
    MotionCategory.SKIN: (255, 205, 60, 255),
    MotionCategory.INFILL: (62, 166, 255, 255),
    MotionCategory.SUPPORT: (145, 94, 255, 255),
    MotionCategory.SUPPORT_INTERFACE: (190, 120, 255, 255),
    MotionCategory.TRAVEL: (65, 210, 170, 255),
    MotionCategory.RETRACTION: (30, 30, 30, 255),
    MotionCategory.UNRETRACTION: (90, 90, 90, 255),
}


def _heat_color(intensity: float) -> tuple[int, int, int, int]:
    value = max(0.0, min(1.0, intensity))
    if value < 0.5:
        ratio = value * 2
        return (int(30 * (1 - ratio) + 255 * ratio), int(130 * (1 - ratio) + 210 * ratio), int(255 * (1 - ratio) + 40 * ratio), 255)
    ratio = (value - 0.5) * 2
    return (255, int(210 * (1 - ratio) + 35 * ratio), int(40 * (1 - ratio) + 35 * ratio), 255)


def _value(point, mode: HeatmapMode) -> float:
    if mode == HeatmapMode.TRAVEL:
        return point.estimated_time_seconds if point.category == MotionCategory.TRAVEL else 0.0
    if mode == HeatmapMode.RETRACTION:
        return point.estimated_time_seconds if point.category in (MotionCategory.RETRACTION, MotionCategory.UNRETRACTION) else 0.0
    if mode == HeatmapMode.CATEGORY:
        return 1.0
    return point.estimated_time_seconds


def build_heatmap(result: AnalysisRun, mode: HeatmapMode = HeatmapMode.TIME, layer_index: int | None = None) -> list[HeatmapPoint]:
    segments = [segment for layer in result.layers for segment in layer.segments if layer_index is None or layer.index == layer_index]
    maximum = max((_value(segment, mode) for segment in segments), default=0.0)
    points: list[HeatmapPoint] = []
    for segment in segments:
        value = _value(segment, mode)
        intensity = value / maximum if maximum else 0.0
        color = _CATEGORY_COLORS.get(segment.category, _heat_color(intensity)) if mode == HeatmapMode.CATEGORY else _heat_color(intensity)
        points.append(HeatmapPoint(
            layer_index=segment.layer_index,
            x_start_mm=segment.x_start_mm,
            y_start_mm=segment.y_start_mm,
            z_start_mm=segment.z_start_mm,
            x_end_mm=segment.x_end_mm,
            y_end_mm=segment.y_end_mm,
            z_end_mm=segment.z_end_mm,
            category=segment.category,
            estimated_time_seconds=segment.estimated_time_seconds,
            intensity=intensity,
            color_rgba=color,
        ))
    return points
