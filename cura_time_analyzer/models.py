"""Pure-Python domain models for Cura Time Analyzer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4


class MotionCategory(str, Enum):
    WALL_OUTER = "wall_outer"
    WALL_INNER = "wall_inner"
    SKIN = "skin"
    INFILL = "infill"
    SUPPORT = "support"
    SUPPORT_INTERFACE = "support_interface"
    SKIRT_BRIM_RAFT = "skirt_brim_raft"
    TRAVEL = "travel"
    RETRACTION = "retraction"
    UNRETRACTION = "unretraction"
    TOOL_CHANGE = "tool_change"
    HEATING = "heating"
    PAUSE = "pause"
    OTHER = "other"
    UNKNOWN = "unknown"


@dataclass
class ParserWarning:
    line_number: int
    message: str


@dataclass
class LayerStats:
    index: int
    z_height_mm: float = 0.0
    total_time_seconds: float = 0.0
    extrusion_time_seconds: float = 0.0
    travel_time_seconds: float = 0.0
    auxiliary_time_seconds: float = 0.0
    distance_extrusion_mm: float = 0.0
    distance_travel_mm: float = 0.0
    retraction_count: int = 0
    move_count: int = 0
    category_times: dict[MotionCategory, float] = field(default_factory=dict)
    category_distances: dict[MotionCategory, float] = field(default_factory=dict)

    def add(self, category: MotionCategory, seconds: float, distance: float, extrusion: float) -> None:
        self.total_time_seconds += seconds
        self.move_count += 1
        self.category_times[category] = self.category_times.get(category, 0.0) + seconds
        self.category_distances[category] = self.category_distances.get(category, 0.0) + distance
        if category in (MotionCategory.TRAVEL, MotionCategory.RETRACTION, MotionCategory.UNRETRACTION):
            self.travel_time_seconds += seconds
            self.distance_travel_mm += distance
        elif extrusion > 0:
            self.extrusion_time_seconds += seconds
            self.distance_extrusion_mm += extrusion
        else:
            self.auxiliary_time_seconds += seconds
        if category == MotionCategory.RETRACTION:
            self.retraction_count += 1

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["category_times"] = {key.value: value for key, value in self.category_times.items()}
        data["category_distances"] = {key.value: value for key, value in self.category_distances.items()}
        return data


@dataclass
class GlobalStats:
    total_time_seconds: float = 0.0
    distance_extrusion_mm: float = 0.0
    distance_travel_mm: float = 0.0
    retraction_count: int = 0
    move_count: int = 0
    category_times: dict[MotionCategory, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["category_times"] = {key.value: value for key, value in self.category_times.items()}
        return data


@dataclass
class ParameterCandidate:
    key: str
    label_key: str


@dataclass
class Evidence:
    metric: str
    value: float
    unit: str


@dataclass
class Recommendation:
    id: str
    severity: str
    title_key: str
    explanation_key: str
    evidence: list[Evidence] = field(default_factory=list)
    parameter_candidates: list[ParameterCandidate] = field(default_factory=list)
    confidence: str = "medium"
    reversible: bool = True


@dataclass
class AnalysisRun:
    analysis_run_id: str = field(default_factory=lambda: str(uuid4()))
    schema_version: str = "1.0"
    estimator_mode: str = "fast"
    total_time_seconds: float = 0.0
    layer_count: int = 0
    global_stats: GlobalStats = field(default_factory=GlobalStats)
    layers: list[LayerStats] = field(default_factory=list)
    recommendations: list[Recommendation] = field(default_factory=list)
    parser_warnings: list[ParserWarning] = field(default_factory=list)
    input_metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "analysis_run_id": self.analysis_run_id,
            "estimator_mode": self.estimator_mode,
            "total_time_seconds": self.total_time_seconds,
            "layer_count": self.layer_count,
            "global_stats": self.global_stats.to_dict(),
            "layers": [layer.to_dict() for layer in self.layers],
            "recommendations": [
                {
                    "id": item.id,
                    "severity": item.severity,
                    "title_key": item.title_key,
                    "explanation_key": item.explanation_key,
                    "evidence": [asdict(evidence) for evidence in item.evidence],
                    "parameter_candidates": [asdict(candidate) for candidate in item.parameter_candidates],
                    "confidence": item.confidence,
                    "reversible": item.reversible,
                }
                for item in self.recommendations
            ],
            "parser_warnings": [asdict(warning) for warning in self.parser_warnings],
            "input_metadata": self.input_metadata,
        }
