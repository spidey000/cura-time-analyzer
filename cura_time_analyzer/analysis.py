"""Streaming G-code parser and fast time estimator."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Iterable

from .models import AnalysisRun, GlobalStats, LayerStats, MotionCategory, MotionSegment, ParserWarning

_TOKEN_RE = re.compile(r"([A-Za-z])([-+]?\d*\.?\d+)")


@dataclass
class _State:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    e: float = 0.0
    feed_rate: float = 1200.0
    absolute_xyz: bool = True
    absolute_e: bool = True
    layer_index: int | None = None
    z_height: float = 0.0
    feature: MotionCategory = MotionCategory.UNKNOWN


def _tokens(line: str) -> dict[str, float]:
    return {key.upper(): float(value) for key, value in _TOKEN_RE.findall(line.upper())}


def _feature_from_comment(comment: str) -> MotionCategory | None:
    value = comment.upper().replace("_", "-")
    if "WALL-OUTER" in value or "OUTER-WALL" in value:
        return MotionCategory.WALL_OUTER
    if "WALL-INNER" in value or "INNER-WALL" in value:
        return MotionCategory.WALL_INNER
    if "SUPPORT-INTERFACE" in value:
        return MotionCategory.SUPPORT_INTERFACE
    if "SUPPORT" in value:
        return MotionCategory.SUPPORT
    if "SKIN" in value or "TOP/BOTTOM" in value:
        return MotionCategory.SKIN
    if "INFILL" in value:
        return MotionCategory.INFILL
    if "SKIRT" in value or "BRIM" in value or "RAFT" in value:
        return MotionCategory.SKIRT_BRIM_RAFT
    return None


def _ensure_layer(layers: dict[int, LayerStats], state: _State) -> LayerStats:
    index = state.layer_index if state.layer_index is not None else 0
    layer = layers.setdefault(index, LayerStats(index=index, z_height_mm=state.z_height))
    if state.z_height:
        layer.z_height_mm = state.z_height
    return layer


def analyze_lines(lines: Iterable[str]) -> AnalysisRun:
    state = _State()
    layers: dict[int, LayerStats] = {}
    global_stats = GlobalStats()
    warnings: list[ParserWarning] = []
    previous_comment = ""

    for line_number, raw_line in enumerate(lines, 1):
        line = raw_line.strip()
        if not line:
            continue
        code, _, comment = line.partition(";")
        comment = comment.strip()
        if comment:
            previous_comment = comment
            layer_match = re.search(r"(?:LAYER|LAYER_COUNT)\s*:\s*(-?\d+)", comment, re.I)
            if layer_match and comment.upper().startswith("LAYER:"):
                state.layer_index = int(layer_match.group(1))
            z_match = re.search(r"(?:Z|LAYER_HEIGHT)\s*:\s*(-?\d+(?:\.\d+)?)", comment, re.I)
            if z_match and comment.upper().startswith(("Z:", "LAYER_HEIGHT:")):
                state.z_height = float(z_match.group(1))
            feature = _feature_from_comment(comment)
            if feature:
                state.feature = feature
        code = code.strip().upper()
        if not code:
            continue
        command = code.split()[0]
        values = _tokens(code)

        if command in {"G90", "G91"}:
            state.absolute_xyz = command == "G90"
            continue
        if command in {"M82", "M83"}:
            state.absolute_e = command == "M82"
            continue
        if command.startswith("T") and command[1:].isdigit():
            layer = _ensure_layer(layers, state)
            layer.add(MotionCategory.TOOL_CHANGE, 0.0, 0.0, 0.0)
            global_stats.category_times[MotionCategory.TOOL_CHANGE] = global_stats.category_times.get(MotionCategory.TOOL_CHANGE, 0.0)
            continue
        if command in {"M104", "M109", "M140", "M190"}:
            layer = _ensure_layer(layers, state)
            layer.add(MotionCategory.HEATING, 0.0, 0.0, 0.0)
            continue
        if command in {"M0", "M1", "M25"}:
            layer = _ensure_layer(layers, state)
            layer.add(MotionCategory.PAUSE, 0.0, 0.0, 0.0)
            continue
        if command not in {"G0", "G00", "G1", "G01"}:
            if command[0:1] in {"G", "M"} and command not in {"G92"}:
                warnings.append(ParserWarning(line_number, f"Comando no analizado: {command}"))
            if command == "G92":
                state.x = values.get("X", state.x)
                state.y = values.get("Y", state.y)
                state.z = values.get("Z", state.z)
                state.e = values.get("E", state.e)
            continue

        if "F" in values:
            if values["F"] > 0:
                state.feed_rate = values["F"]
        old = (state.x, state.y, state.z, state.e)
        new_x = values.get("X", state.x) if state.absolute_xyz else state.x + values.get("X", 0.0)
        new_y = values.get("Y", state.y) if state.absolute_xyz else state.y + values.get("Y", 0.0)
        new_z = values.get("Z", state.z) if state.absolute_xyz else state.z + values.get("Z", 0.0)
        new_e = values.get("E", state.e) if state.absolute_e else state.e + values.get("E", 0.0)
        distance = math.sqrt((new_x - old[0]) ** 2 + (new_y - old[1]) ** 2 + (new_z - old[2]) ** 2)
        delta_e = new_e - old[3]
        speed = max(state.feed_rate / 60.0, 0.001)
        moved_time = distance / speed
        e_distance = abs(delta_e)
        if distance == 0 and e_distance > 0:
            moved_time = e_distance / speed
            category = MotionCategory.RETRACTION if delta_e < 0 else MotionCategory.UNRETRACTION
        elif delta_e > 0:
            category = state.feature if state.feature != MotionCategory.UNKNOWN else MotionCategory.OTHER
        else:
            category = MotionCategory.TRAVEL
        state.x, state.y, state.z, state.e = new_x, new_y, new_z, new_e
        if new_z:
            state.z_height = new_z
        layer = _ensure_layer(layers, state)
        layer.add(category, moved_time, distance, delta_e)
        layer.segments.append(MotionSegment(
            layer_index=layer.index,
            x_start_mm=old[0], y_start_mm=old[1], z_start_mm=old[2],
            x_end_mm=new_x, y_end_mm=new_y, z_end_mm=new_z,
            category=category,
            distance_mm=distance,
            extrusion_delta_mm=delta_e,
            estimated_time_seconds=moved_time,
            feed_rate_mm_min=state.feed_rate,
        ))
        global_stats.total_time_seconds += moved_time
        global_stats.move_count += 1
        global_stats.distance_extrusion_mm += max(delta_e, 0.0)
        global_stats.distance_travel_mm += distance if category == MotionCategory.TRAVEL else 0.0
        global_stats.retraction_count += int(category == MotionCategory.RETRACTION)
        global_stats.category_times[category] = global_stats.category_times.get(category, 0.0) + moved_time

    ordered = [layers[index] for index in sorted(layers)]
    return AnalysisRun(
        total_time_seconds=sum(layer.total_time_seconds for layer in ordered),
        layer_count=len(ordered),
        global_stats=global_stats,
        layers=ordered,
        parser_warnings=warnings,
    )
