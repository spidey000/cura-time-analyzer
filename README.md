# Cura Time Analyzer

Plugin de UltiMaker Cura para analizar el tiempo estimado de impresión por capa y por tipo de movimiento.

## Estado

**Fase actual:** diseño técnico.

El alcance inicial es **A: análisis del G-code y recomendaciones**, dejando preparadas las estructuras internas para:

- **B:** comparación entre perfiles o análisis.
- **C:** aplicación asistida de cambios sin sobrescribir el perfil original.

Todavía no se ha implementado el plugin ejecutable.

## Documentación

- [Diseño técnico](docs/design.md)

## Principios

- Analizar el G-code sin modificarlo en el MVP.
- Separar parser, motor de estimación, recomendaciones e interfaz.
- Mantener recomendaciones explicables.
- Ejecutar el análisis sin bloquear la interfaz de Cura.
- Declarar claramente que el resultado inicial es una estimación.
