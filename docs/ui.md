# UI del MVP

La interfaz del MVP usa **Qt Widgets**, disponible dentro del entorno de Cura, para reducir dependencias y facilitar una primera versión estable. La lógica no está mezclada con la UI.

## Módulos

```text
Cura menu
  └── CuraTimeAnalyzerExtension
        └── AnalysisDialog
              ├── Summary section
              ├── Layer table
              ├── Layer detail section
              ├── Recommendation list
              └── Export actions
```

### `CuraTimeAnalyzerExtension`

Solo integra el plugin con el menú de Cura y abre el diálogo. No analiza G-code ni conoce las reglas de recomendación.

### `AnalysisDialog`

Responsabilidades:

- Seleccionar un G-code.
- Presentar el resumen.
- Mostrar capas ordenables/seleccionables.
- Mostrar el detalle de la capa seleccionada.
- Mostrar recomendaciones.
- Delegar el análisis y la exportación en `AnalysisController`.

### `AnalysisController`

Es la frontera entre UI y dominio. En versiones futuras podrá recibir dos `AnalysisRun` para comparación sin rehacer el diálogo ni el parser.

## Flujo actual

1. En Cura: menú **Extensions → Analizar tiempo por capa…**.
2. Pulsar **Analizar G-code…**.
3. Seleccionar el archivo `.gcode`, `.gco` o `.g`.
4. Revisar resumen, capas, detalle y recomendaciones.
5. Exportar JSON o CSV.

## Decisiones para futuras versiones

- Añadir un gráfico de tiempo por capa como widget independiente.
- Sustituir textos internos por catálogo de traducciones.
- Añadir un selector de análisis guardados para B.
- Añadir una vista de `ProfileChangeSet` para C.
- Mantener el diálogo como shell de presentación y no mover lógica al QML.
