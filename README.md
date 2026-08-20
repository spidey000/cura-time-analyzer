# Cura Time Analyzer

Plugin de UltiMaker Cura para analizar el tiempo estimado de impresión por capa y por tipo de movimiento.

## Estado

**Versión:** 0.2.0 — heatmap y análisis what-if.

Incluye análisis local de G-code, desglose por capa/categoría, recomendaciones explicables, exportación JSON/CSV, soporte `.gx`, segmentos de toolpath y heatmap 2D por capa. La arquitectura deja preparados `AnalysisRun`, `ComparisonRun` y `ProfileChangeSet` para las versiones B y C.

## Documentación

- [Diseño técnico](docs/design.md)
- [Diseño de UI](docs/ui.md)

## Uso

1. Ejecutar `python scripts/package_plugin.py`.
2. En Cura, abrir **Help → Show Configuration Folder**.
3. Copiar `dist/CuraTimeAnalyzer.plugin` al directorio de plugins de Cura o instalarlo mediante el gestor de paquetes si la versión lo permite.
4. Reiniciar Cura.
5. Abrir **Extensions → Analizar tiempo por capa…**.
6. Seleccionar el G-code y exportar el análisis si se necesita.

El paquete declara compatibilidad con SDK `6.5.0`, que debe ajustarse si se quiere soportar otra rama mayor de Cura.

## Principios

- Analizar el G-code sin modificarlo en el MVP.
- Separar parser, motor de estimación, recomendaciones e interfaz.
- Mantener recomendaciones explicables.
- Ejecutar el análisis sin bloquear la interfaz de Cura.
- Declarar claramente que el resultado inicial es una estimación.
