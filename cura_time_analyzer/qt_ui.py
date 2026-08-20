"""Small Qt Widgets UI kept independent from the analysis domain."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .controller import AnalysisController
from .heatmap import HeatmapMode, HeatmapPoint, build_heatmap
from .models import MotionCategory

try:
    # Cura 5.x / SDK 8.x uses PyQt6.
    from PyQt6.QtCore import QTimer, Qt
    from PyQt6.QtGui import QColor, QPainter, QPen
    from PyQt6.QtWidgets import (
        QComboBox, QDialog, QFileDialog, QGridLayout, QGroupBox, QHBoxLayout, QLabel,
        QListWidget, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout,
        QWidget, QAbstractItemView,
    )
    _ALIGN_CENTER = Qt.AlignmentFlag.AlignCenter
    _SELECT_ROWS = QAbstractItemView.SelectionBehavior.SelectRows
except ImportError:
    # Keep repository-side tests importable without Cura's bundled Qt.
    QDialog = object  # type: ignore[misc,assignment]
    QWidget = object  # type: ignore[misc,assignment]
    _ALIGN_CENTER = 0
    _SELECT_ROWS = 0


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


class ToolpathHeatmapView(QWidget):
    """2D top-down toolpath heatmap; ready to be replaced by a Cura scene adapter."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._points: list[HeatmapPoint] = []
        self.setMinimumHeight(260)

    def set_points(self, points: list[HeatmapPoint]) -> None:
        self._points = points
        self.update()

    def paintEvent(self, event):  # pragma: no cover - exercised inside Cura Qt
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0))
        if not self._points:
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(self.rect(), _ALIGN_CENTER, "Selecciona un G-code y una capa")
            return
        xs = [value for point in self._points for value in (point.x_start_mm, point.x_end_mm)]
        ys = [value for point in self._points for value in (point.y_start_mm, point.y_end_mm)]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        scale_x = (self.width() - 24) / max(max_x - min_x, 1.0)
        scale_y = (self.height() - 24) / max(max_y - min_y, 1.0)
        scale = min(scale_x, scale_y)
        offset_x = (self.width() - (max_x - min_x) * scale) / 2
        offset_y = (self.height() - (max_y - min_y) * scale) / 2
        for point in self._points:
            color = point.color_rgba
            painter.setPen(QPen(Qt.white if color[0] + color[1] + color[2] < 240 else Qt.black, 1))
            painter.setPen(QPen(QColor(*color), 2))
            x1 = offset_x + (point.x_start_mm - min_x) * scale
            y1 = self.height() - (offset_y + (point.y_start_mm - min_y) * scale)
            x2 = offset_x + (point.x_end_mm - min_x) * scale
            y2 = self.height() - (offset_y + (point.y_end_mm - min_y) * scale)
            painter.drawLine(round(x1), round(y1), round(x2), round(y2))


class AnalysisDialog(QDialog):
    """MVP dialog: choose G-code, inspect layers, export results."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cura Time Analyzer")
        self.resize(900, 620)
        self.controller = AnalysisController()
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="cura-time-analyzer")
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
        self.layer_table.setSelectionBehavior(_SELECT_ROWS)
        self.layer_table.itemSelectionChanged.connect(self._show_layer_detail)
        root.addWidget(self.layer_table)

        heatmap_controls = QHBoxLayout()
        heatmap_controls.addWidget(QLabel("Heatmap:"))
        self.heatmap_mode = QComboBox()
        for label, mode in (("Tiempo", HeatmapMode.TIME), ("Travel", HeatmapMode.TRAVEL), ("Retracciones", HeatmapMode.RETRACTION), ("Categoría", HeatmapMode.CATEGORY)):
            self.heatmap_mode.addItem(label, mode)
        self.heatmap_mode.currentIndexChanged.connect(self._refresh_heatmap)
        heatmap_controls.addWidget(self.heatmap_mode)
        heatmap_controls.addStretch()
        root.addLayout(heatmap_controls)
        self.heatmap_view = ToolpathHeatmapView()
        root.addWidget(self.heatmap_view)

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
        future = self._executor.submit(self.controller.analyze_file, path)
        future.add_done_callback(self._analysis_finished)
        self.warning_label.setText("Analizando en segundo plano… Cura sigue disponible.")

    def _analysis_finished(self, future):
        try:
            result = future.result()
        except (OSError, UnicodeError, ValueError) as exc:
            message = str(exc)
            QTimer.singleShot(0, lambda: QMessageBox.critical(self, "No se pudo analizar", message))
            return
        QTimer.singleShot(0, lambda: self._present_result(result))

    def _present_result(self, result):
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
        self.warning_label.setText("Estimación rápida basada en el G-code; puede variar respecto al tiempo real.")
        self.layer_table.resizeColumnsToContents()
        self._refresh_heatmap()

    def _refresh_heatmap(self):
        if not self.controller.last_result:
            self.heatmap_view.set_points([])
            return
        rows = self.layer_table.selectionModel().selectedRows()
        layer_index = self.controller.last_result.layers[rows[0].row()].index if rows else None
        mode = self.heatmap_mode.currentData()
        self.heatmap_view.set_points(build_heatmap(self.controller.last_result, mode, layer_index))

    def _show_layer_detail(self):
        rows = self.layer_table.selectionModel().selectedRows()
        if not rows or not self.controller.last_result:
            return
        layer = self.controller.last_result.layers[rows[0].row()]
        parts = [f"Capa {layer.index} · {layer.z_height_mm:.3f} mm · {_duration(layer.total_time_seconds)}"]
        for category, seconds in sorted(layer.category_times.items(), key=lambda item: item[1], reverse=True):
            parts.append(f"{_CATEGORY_LABELS.get(category, category.value)}: {_duration(seconds)}")
        self.detail_label.setText("\n".join(parts))
        self._refresh_heatmap()

    def closeEvent(self, event):
        self._executor.shutdown(wait=False, cancel_futures=True)
        super().closeEvent(event)

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
