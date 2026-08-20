# Changelog

## 0.2.3 — 2026-08-20

- Removed the legacy PyQt5 fallback.
- Targeted only Cura SDK 8.9.0 / Cura 5.9.x.

## 0.2.2 — 2026-08-20

- Targeted the latest verified Marketplace SDK entry: `8.9.0`.
- Removed older SDK declarations to prevent ambiguous Marketplace validation.

## 0.2.1 — 2026-08-20

- Added Cura SDK 8.0.0–8.9.0 metadata.
- Added PyQt6 support for Cura 5.x with PyQt5 fallback.
- Adapted Qt alignment and selection enums for PyQt6.
- Added static compatibility tests for the SDK 8.x declaration.

## 0.2.0 — 2026-08-20

- Añadido soporte para archivos FlashForge `.gx` / XGCode.
- Añadidos segmentos de toolpath con coordenadas y tiempo estimado.
- Añadido heatmap 2D por tiempo, travel, retracciones y categoría.
- Añadido análisis what-if para cambios de velocidad.
- El análisis de archivos grandes se ejecuta en segundo plano.
- Corregido el registro del menú de la extensión.

## 0.1.0 — 2026-08-20

- Primera versión del analizador por capas.
- Desglose por categorías y recomendaciones explicables.
- Exportación JSON y CSV.
