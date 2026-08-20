"""Small Qt Widgets UI kept independent from the analysis domain."""

from __future__ import annotations

from pathlib import Path

from .controller import AnalysisController
from .models import MotionCategory

try:
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import (
        QDialog, QFileDialog, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QListWidget,
        QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout,
    )
except ImportError:  # pragma: no cover - only imported inside Cura
    QDialog = object  # type: ignore[misc,assignment]


_CATEGORY_LABELS = {
    MotionCategory.WALL_OUTER: "Pared exterior",
    MotionCategory.WALL_INNER: "Pared interior",
    MotionCategory.SKIN: "Superficie",
    MotionCategory.INFILL: "Relleno",
    MotionCategory.SUPPORT: "Soporte",
    MotionCategory.SUPPORT_INTERFACE: "Interfaz de soporte",
    MotionCategory.SKIRT_BRIM_RAFT: "Skirt / brim / raft",
    MotionCategory.TRAVEL: "Travel",
    MotionCategory.RETRACTION: "Retracción",
    MotionCategory.UNRETRACTION: "Desretracción",
    MotionCategory.TOOL_CHANGE: "Cambio de herramienta",
    MotionCategory.HEATING: "Calentamiento",
    MotionCategory.PAUSE: "Pausa",
    MotionCategory.OTHER: "Otros",
    MotionCategory.UNKNOWN: "Desconocido",
}


def _duration(seconds: float) -> str:
    minutes = int(round(seconds / 60))
    return f"{minutes // 60} h {minutes % 60:02d} min"


class AnalysisDialog(QDialog):
    """MVP dialog: choose G-code, inspect layers, export results."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cura Time Analyzer")
        self.resize(900, 620)
        self.controller = AnalysisController()
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        actions = QHBoxLayout()
        open_button = QPushButton("Analizar G-code…")
        open_button.clicked.connect(self._choose_file)
        json_button = QPushButton("Exportar JSON")
        json_button.clicked.connect(self._export_json)
        csv_button = QPushButton("Exportar CSV")
        csv_button.clicked.connect(self._export_csv)
        actions.addWidget(open_button)
        actions.addWidget(json_button)
        actions.addWidget(csv_button)
        actions.addStretch()
        root.addLayout(actions)

        summary = QGroupBox("Resumen")
        summary_layout = QGridLayout(summary)
        self.total_label = QLabel("—")
        self.layers_label = QLabel("—")
        self.slowest_label = QLabel("—")
        self.warning_label = QLabel("Estimación rápida basada en el G-code; puede variar respecto al tiempo real.")
        self.warning_label.setWordWrap(True)
        summary_layout.addWidget(QLabel("Tiempo total"), 0, 0)
        summary_layout.addWidget(self.total_label, 0, 1)
        summary_layout.addWidget(QLabel("Capas"), 0, 2)
        summary_layout.addWidget(self.layers_label, 0, 3)
        summary_layout.addWidget(QLabel("Capa más lenta"), 0, 4)
        summary_layout.addWidget(self.slowest_label, 0, 5)
        summary_layout.addWidget(self.warning_label, 1, 0, 1, 6)
        root.addWidget(summary)

        self.layer_table = QTableWidget(0, 8)
        self.layer_table.setHorizontalHeaderLabels(["Capa", "Z (mm)", "Tiempo", "% total", "Extrusión", "Travel", "Retracciones", "Dominante"])
        self.layer_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.layer_table.itemSelectionChanged.connect(self._show_layer_detail)
        root.addWidget(self.layer_table)

        detail_layout = QHBoxLayout()
        self.detail_label = QLabel("Selecciona una capa para ver el desglose.")
        self.detail_label.setWordWrap(True)
        detail_layout.addWidget(self.detail_label, 2)
        self.recommendations = QListWidget()
        detail_layout.addWidget(self.recommendations, 3)
        root.addLayout(detail_layout)

    def _choose_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar G-code", "", "G-code (*.gcode *.gco *.g *.gx);;Todos (*.*)")
        if not path:
            return
        try:
            result = self.controller.analyze_file(path)
        except (OSError, UnicodeError, ValueError) as exc:
            QMessageBox.critical(self, "No se pudo analizar", str(exc))
            return
        self.total_label.setText(_duration(result.total_time_seconds))
        self.layers_label.setText(str(result.layer_count))
        slowest = max(result.layers, key=lambda layer: layer.total_time_seconds, default=None)
        self.slowest_label.setText(f"{slowest.index} — {_duration(slowest.total_time_seconds)}" if slowest else "—")
        self.layer_table.setRowCount(len(result.layers))
        for row, layer in enumerate(result.layers):
            dominant = max(layer.category_times, key=layer.category_times.get, default=MotionCategory.UNKNOWN)
            values = [
                str(layer.index), f"{layer.z_height_mm:.3f}", _duration(layer.total_time_seconds),
                f"{layer.total_time_seconds / result.total_time_seconds * 100:.1f}%" if result.total_time_seconds else "0%",
                _duration(layer.extrusion_time_seconds), _duration(layer.travel_time_seconds), str(layer.retraction_count),
                _CATEGORY_LABELS.get(dominant, dominant.value),
            ]
            for column, value in enumerate(values):
                self.layer_table.setItem(row, column, QTableWidgetItem(value))
        self.recommendations.clear()
        for item in result.recommendations:
            keys = ", ".join(candidate.key for candidate in item.parameter_candidates)
            self.recommendations.addItem(f"{item.id}: revisar {keys}")
        self.layer_table.resizeColumnsToContents()

    def _show_layer_detail(self):
        rows = self.layer_table.selectionModel().selectedRows()
        if not rows or not self.controller.last_result:
            return
        layer = self.controller.last_result.layers[rows[0].row()]
        parts = [f"Capa {layer.index} · {layer.z_height_mm:.3f} mm · {_duration(layer.total_time_seconds)}"]
        for category, seconds in sorted(layer.category_times.items(), key=lambda item: item[1], reverse=True):
            parts.append(f"{_CATEGORY_LABELS.get(category, category.value)}: {_duration(seconds)}")
        self.detail_label.setText("\n".join(parts))

    def _export_json(self):
        if not self.controller.last_result:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Exportar análisis JSON", "analysis.json", "JSON (*.json)")
        if path:
            self.controller.export_json(path)

    def _export_csv(self):
        if not self.controller.last_result:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Exportar capas CSV", "layers.csv", "CSV (*.csv)")
        if path:
            self.controller.export_csv(path)
