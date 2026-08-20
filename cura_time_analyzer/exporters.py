"""Export analysis results without leaking source G-code."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from .models import AnalysisRun


def write_json(result: AnalysisRun, path: str | Path) -> None:
    Path(path).write_text(json.dumps(result.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")


def write_csv(result: AnalysisRun, path: str | Path) -> None:
    categories = sorted({key.value for layer in result.layers for key in layer.category_times})
    fields = ["layer", "z_height_mm", "total_time_seconds", "travel_time_seconds", "extrusion_time_seconds", "retraction_count", *categories]
    with Path(path).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for layer in result.layers:
            row = {
                "layer": layer.index,
                "z_height_mm": f"{layer.z_height_mm:.4f}",
                "total_time_seconds": f"{layer.total_time_seconds:.4f}",
                "travel_time_seconds": f"{layer.travel_time_seconds:.4f}",
                "extrusion_time_seconds": f"{layer.extrusion_time_seconds:.4f}",
                "retraction_count": layer.retraction_count,
            }
            row.update({key.value: f"{value:.4f}" for key, value in layer.category_times.items()})
            writer.writerow(row)
