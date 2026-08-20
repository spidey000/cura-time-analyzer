# Cura Time Analyzer — Diseño técnico

**Estado:** propuesta para aprobación

**Objetivo:** analizar el G-code generado por Cura y explicar el tiempo consumido por cada capa y por cada categoría de movimiento, produciendo recomendaciones accionables sin modificar todavía los perfiles.

**Alcance inicial:** A — análisis y recomendaciones.

**Extensibilidad prevista:** B — comparación de análisis/perfiles; C — aplicación asistida de cambios mediante copias de perfiles.

---

## 1. Problema

La estimación total de Cura no explica qué capas consumen más tiempo ni qué factores contribuyen a ese tiempo. El usuario necesita poder responder:

- ¿Qué capas son las más lentas?
- ¿Cuánto tiempo consume cada capa?
- ¿El tiempo está en paredes, relleno, soportes, travel o retracciones?
- ¿Qué parámetros de Cura están relacionados con el coste observado?
- ¿Qué cambio conviene probar sin alterar el perfil original?

## 2. No objetivos del MVP

El MVP no hará lo siguiente:

- No modificará automáticamente perfiles de Cura.
- No sobrescribirá G-code.
- No simulará con exactitud el firmware de cada impresora.
- No medirá el tiempo real de la impresora.
- No se conectará a impresoras ni a servicios externos.
- No optimizará la geometría del modelo.
- No usará aprendizaje automático.

## 3. Flujo de usuario

```text
1. El usuario configura Cura y ejecuta Slice.
2. El plugin detecta que existe un G-code analizable.
3. El usuario abre «Analizar impresión».
4. El analizador procesa el G-code fuera del hilo de UI.
5. Se muestra un resumen global.
6. El usuario selecciona una capa para ver el desglose.
7. El plugin muestra factores relacionados y recomendaciones.
8. El usuario exporta CSV/JSON si lo necesita.
9. El usuario modifica Cura manualmente y vuelve a laminar.
```

## 4. Arquitectura

```text
Cura / QML UI
    │
    ▼
AnalysisController ───── AnalysisStore
    │
    ▼
AnalysisJob (background)
    │
    ├── GCodeParser
    │      └── MotionClassifier
    │
    ├── TimeEstimator
    │
    ├── Aggregator
    │      ├── GlobalStats
    │      ├── LayerStats
    │      └── CategoryStats
    │
    └── RecommendationEngine
```

### 4.1 Separación de responsabilidades

- **UI/QML:** presentación, selección, filtros y acciones.
- **AnalysisController:** ciclo de vida de análisis y comunicación con Cura.
- **AnalysisJob:** ejecución asíncrona, progreso, cancelación y errores.
- **GCodeParser:** convierte líneas G-code en eventos normalizados.
- **MotionClassifier:** asigna categorías a movimientos sin calcular recomendaciones.
- **TimeEstimator:** calcula duración estimada según el modo seleccionado.
- **Aggregator:** produce estadísticas inmutables por análisis y capa.
- **RecommendationEngine:** transforma estadísticas en recomendaciones explicables.
- **AnalysisStore:** conserva el último resultado y permite preparar comparaciones futuras.
- **Exporters:** CSV y JSON, sin lógica de análisis.

## 5. Modelo de dominio

### 5.1 AnalysisRun

Representa una ejecución completa y será la unidad de comparación futura.

```text
AnalysisRun
- id: UUID
- created_at: datetime
- source_path: str opcional
- cura_version: str opcional
- sdk_version: str opcional
- printer_definition_id: str opcional
- profile_snapshot: ProfileSnapshot opcional
- estimator_mode: fast | kinematic
- total_time_seconds: float
- layer_count: int
- global_stats: GlobalStats
- layers: list[LayerStats]
- recommendations: list[Recommendation]
- parser_warnings: list[ParserWarning]
```

No se guardará el G-code completo dentro del resultado. Se conservarán metadatos y estadísticas.

### 5.2 MotionEvent

```text
MotionEvent
- line_number: int
- layer_index: int | None
- z_height_mm: float | None
- command: str
- category: MotionCategory
- x_start_mm, y_start_mm: float | None
- x_end_mm, y_end_mm: float | None
- z_start_mm, z_end_mm: float | None
- extrusion_delta_mm: float
- distance_mm: float
- feed_rate_mm_min: float | None
- estimated_time_seconds: float
- source_feature: str | None
```

### 5.3 Categorías

El clasificador debe usar valores estables, no textos traducidos:

```text
WALL_OUTER
WALL_INNER
SKIN
INFILL
SUPPORT
SUPPORT_INTERFACE
SKIRT_BRIM_RAFT
TRAVEL
RETRACTION
UNRETRACTION
TOOL_CHANGE
HEATING
PAUSE
OTHER
UNKNOWN
```

La UI traducirá estas categorías para mostrarlas al usuario.

### 5.4 LayerStats

```text
LayerStats
- index: int
- z_height_mm: float
- total_time_seconds: float
- extrusion_time_seconds: float
- travel_time_seconds: float
- auxiliary_time_seconds: float
- distance_extrusion_mm: float
- distance_travel_mm: float
- retraction_count: int
- move_count: int
- category_times: dict[MotionCategory, float]
- category_distances: dict[MotionCategory, float]
- dominant_categories: list[MotionCategory]
```

### 5.5 Recommendation

```text
Recommendation
- id: str estable
- severity: info | suggestion | warning
- title_key: str de traducción
- explanation_key: str de traducción
- evidence: list[Evidence]
- parameter_candidates: list[ParameterCandidate]
- confidence: low | medium | high
- reversible: bool
```

Una recomendación no ordenará aplicar cambios. Solo describirá evidencia y parámetros candidatos.

### 5.6 Estructuras para B y C

Aunque no se implementen en el MVP:

```text
ComparisonRun
- baseline_analysis_id: UUID
- candidate_analysis_id: UUID
- total_delta_seconds: float
- layer_deltas: list[LayerDelta]
- category_deltas: dict[MotionCategory, float]
- parameter_deltas: list[ParameterDelta]

ProfileChangeSet
- base_profile_id: str
- changes: list[ProfileChange]
- reason: str
- created_copy_id: str | None
- applied: bool
```

Estas estructuras evitan mezclar análisis, comparación y aplicación de cambios.

## 6. Parseo del G-code

El parser reconocerá inicialmente:

- `G0`, `G1`.
- Coordenadas `X`, `Y`, `Z`, `E`.
- Velocidad `F`.
- Cambios de herramienta `T0`, `T1`, etc.
- Retracción y desretracción según el delta de E.
- Marcadores de capa como `;LAYER:` y altura.
- Comentarios de Cura para identificar feature types.
- Modos de coordenadas absolutos/relativos cuando aparezcan (`G90`, `G91`, `M82`, `M83`).
- Calentamiento, espera, pausa y comandos no clasificables.

El parser debe ser tolerante: una línea desconocida genera un `ParserWarning`, no aborta todo el análisis.

### Clasificación

La clasificación preferirá, en este orden:

1. Comentario/feature type explícito de Cura.
2. Movimiento con extrusión o sin extrusión.
3. Contexto de comandos y estado actual.
4. `UNKNOWN` si no hay evidencia suficiente.

No se debe inferir una categoría con certeza cuando solo existe geometría ambigua.

## 7. Estimación del tiempo

### Modo rápido — MVP

```text
distance = longitud del movimiento
speed = feed_rate / 60
raw_time = distance / speed
```

El motor debe acumular tiempo de movimiento, retracción y comandos auxiliares por separado.

### Modo cinemático — fase posterior

Añadirá aceleración, desaceleración, límites por eje y parámetros de firmware. Será una implementación separada detrás de la misma interfaz:

```text
TimeEstimator.estimate(event, machine_constraints) -> TimeEstimate
```

Esto permite cambiar el motor sin modificar parser, agregador ni UI.

### Etiquetado honesto

La UI debe mostrar:

> Estimación basada en G-code. El tiempo real puede variar según firmware, aceleración, calentamiento y pausas.

## 8. Recomendaciones iniciales

Las reglas deben ser deterministas y explicar su evidencia.

### Mucho tiempo en paredes

Candidatos:

- Wall Line Count.
- Outer Wall Speed.
- Inner Wall Speed.
- Layer Height.

### Mucho tiempo en relleno

Candidatos:

- Infill Density.
- Infill Pattern.
- Infill Speed.
- Layer Height.

### Mucho travel

Candidatos:

- Travel Speed.
- Travel Avoid Distance.
- Combing Mode.
- Orden de impresión.

### Muchas retracciones

Candidatos:

- Retraction Distance.
- Retraction Speed.
- Maximum Retraction Count.
- Minimum Travel Distance.

### Mucho soporte

Candidatos:

- Support Density.
- Support Pattern.
- Support Speed.
- Support Placement.

Las reglas no aplicarán cambios en A.

## 9. Interfaz MVP

### Resumen

- Tiempo total.
- Capas.
- Capa más lenta.
- Tiempo medio.
- Advertencia sobre precisión.

### Tabla de capas

Columnas mínimas:

- Capa.
- Altura.
- Tiempo.
- Porcentaje del total.
- Tiempo de extrusión.
- Tiempo de travel.
- Retracciones.
- Categoría dominante.

### Detalle de capa

- Desglose por categoría.
- Evidencia.
- Recomendaciones.
- Enlace a parámetros candidatos.

### Exportación

- CSV de capas.
- JSON del `AnalysisRun`.

## 10. Rendimiento y concurrencia

- El parseo se ejecutará como tarea en segundo plano.
- La UI recibirá progreso por número de líneas o porcentaje.
- Debe existir cancelación cooperativa.
- El resultado solo se publicará cuando el análisis haya finalizado correctamente.
- No se mantendrá en memoria una lista completa de `MotionEvent` si el archivo es grande; el agregador podrá procesar eventos en streaming.

## 11. Compatibilidad

El plugin declarará `supported_sdk_versions` para la versión objetivo de Cura.

La compatibilidad se comprobará en `register(app)` y se mantendrán adaptadores pequeños para diferencias de API. La lógica de parseo debe ser independiente de la versión de Cura.

Objetivo inicial recomendado:

- Una versión estable de Cura instalada en el entorno de desarrollo.
- Python y Qt proporcionados por Cura.
- Sin dependencias externas en el MVP.

## 12. Seguridad y privacidad

- El análisis será local.
- No se enviará G-code a servidores.
- No se incluirá G-code completo en exportaciones por defecto.
- Las rutas locales se podrán omitir o anonimizar en JSON.
- No se añadirán credenciales ni tokens al repositorio.

## 13. Pruebas

### Unitarias

- Parseo de movimientos absolutos y relativos.
- Cambio de capa.
- Extrusión y travel.
- Retracción.
- Cambio de herramienta.
- Líneas desconocidas.
- G-code vacío o incompleto.
- Cálculo de tiempo con velocidad cero o ausente.
- Clasificación por feature type.
- Agregación por capa y categoría.
- Reglas de recomendaciones.

### Fixtures

Se crearán fixtures pequeños y legibles, no modelos completos:

- `simple_cube.gcode`.
- `retractions.gcode`.
- `supports.gcode`.
- `multi_tool.gcode`.
- `relative_coordinates.gcode`.
- `unknown_commands.gcode`.

### Integración

- El plugin carga en Cura.
- El menú/panel aparece.
- Un análisis produce resultado.
- Cancelar no bloquea Cura.
- Exportar CSV/JSON produce archivos válidos.

## 14. Plan de implementación posterior a la aprobación

### Fase 0 — Esqueleto

- Crear estructura de plugin.
- Añadir `plugin.json` y `__init__.py`.
- Registrar una extensión vacía.
- Verificar carga en Cura.

### Fase 1 — Dominio y parser

- Definir enums y dataclasses.
- Crear fixtures.
- Implementar parser streaming.
- Añadir pruebas unitarias.

### Fase 2 — Estimación y agregación

- Implementar modo rápido.
- Agregar por capa y categoría.
- Calcular resumen global.
- Añadir exportación JSON/CSV.

### Fase 3 — Interfaz

- Añadir panel QML.
- Mostrar resumen y tabla.
- Añadir detalle de capa.
- Añadir gráfico sin acoplarlo al parser.

### Fase 4 — Recomendaciones

- Implementar reglas.
- Mostrar evidencia y parámetros candidatos.
- Añadir advertencias de baja confianza.

### Fase 5 — Validación en Cura

- Instalar `.plugin` local.
- Analizar G-code real.
- Comparar resultado con el tiempo mostrado por Cura.
- Documentar discrepancias.

### Fase 6 — Preparación de B y C

- Incorporar `AnalysisRun` persistible.
- Comparar dos ejecuciones.
- Crear `ProfileChangeSet` sin aplicarlo.
- Solo después diseñar aplicación segura sobre copias.

## 15. Criterios de aceptación del MVP

- Cura carga el plugin sin errores.
- El usuario puede analizar el G-code recién generado.
- Se detectan correctamente las capas en los fixtures.
- El tiempo total agregado coincide con la suma de capas, salvo comandos globales documentados.
- Cada capa muestra desglose por categoría.
- Las cinco capas más lentas son identificables.
- Una recomendación incluye evidencia y parámetros candidatos.
- El análisis no congela la UI.
- CSV y JSON se pueden abrir y validar.
- No se modifica el G-code ni el perfil de Cura.
