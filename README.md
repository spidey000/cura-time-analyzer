# Cura Time Analyzer

Plugin de UltiMaker Cura para analizar el tiempo estimado de impresión por capa y por tipo de movimiento.

## Estado

**Versión:** 0.2.1 — compatibilidad SDK 8.x, heatmap y análisis what-if.

Incluye análisis local de G-code, desglose por capa/categoría, recomendaciones explicables, exportación JSON/CSV, soporte `.gx`, segmentos de toolpath y heatmap 2D por capa. La arquitectura deja preparados `AnalysisRun`, `ComparisonRun` y `ProfileChangeSet` para las versiones B y C.

## Documentación

- [Diseño técnico](docs/design.md)
- [Diseño de UI](docs/ui.md)

## Instalación manual sin Marketplace

1. Ejecutar `python scripts/package_plugin.py`.
2. En Cura, abrir **Help → Show Configuration Folder**.
3. Crear dentro una carpeta `plugins` si no existe.
4. Extraer `dist/CuraTimeAnalyzer.plugin` dentro de `plugins/`. Debe quedar `plugins/CuraTimeAnalyzer/plugin.json`.
5. Reiniciar Cura.
6. Abrir **Extensions → Analizar tiempo por capa…**.

En Linux, la carpeta suele estar bajo `~/.local/share/cura/<versión>/`; en Windows bajo la carpeta de datos de Cura del usuario; en macOS bajo `~/Library/Application Support/cura/<versión>/`. Es preferible usar **Show Configuration Folder** porque la ruta exacta depende de la versión y del instalador.

## Publicación en Cura Marketplace

La documentación oficial indica usar [contribute.ultimaker.com](https://contribute.ultimaker.com). El archivo debe ser un ZIP cuya carpeta raíz coincida con el identificador del paquete. El empaquetador del proyecto genera `dist/CuraTimeAnalyzer.plugin` con la carpeta interna `CuraTimeAnalyzer/`.

El paquete declara compatibilidad con la familia SDK `8.0.0`–`8.9.0`, correspondiente a Cura 5.0–5.9 según la documentación oficial. La interfaz intenta primero PyQt6 (Cura 5.x) y mantiene PyQt5 como fallback para instalaciones antiguas.

## Principios

- Analizar el G-code sin modificarlo en el MVP.
- Separar parser, motor de estimación, recomendaciones e interfaz.
- Mantener recomendaciones explicables.
- Ejecutar el análisis sin bloquear la interfaz de Cura.
- Declarar claramente que el resultado inicial es una estimación.
