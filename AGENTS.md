# AGENTS.md — Cura Time Analyzer

## Regla obligatoria

Leer este archivo antes de modificar código, metadatos, empaquetado, documentación o releases del proyecto.

No declarar compatibilidad, publicar una release ni entregar un paquete como funcional sin ejecutar las verificaciones indicadas aquí.

## Proyecto

- Repositorio: https://github.com/spidey000/cura-time-analyzer
- Tipo: plugin de extensión para UltiMaker Cura.
- Licencia: MIT.
- Análisis: local; no enviar G-code, perfiles ni datos del usuario a servicios externos.
- El plugin no modifica G-code y no sobrescribe perfiles originales.

## Versiones objetivo obligatorias

La línea activa del proyecto está orientada a la versión más reciente disponible en el entorno objetivo:

- Cura objetivo: **5.13.x**.
- SDK objetivo: **8.12.0**.
- Qt: **PyQt6 exclusivamente**.
- Python y Qt deben ser los proporcionados por Cura.
- No añadir dependencias externas que Cura no incluya.

`plugin.json` debe declarar exactamente:

```json
"supported_sdk_versions": ["8.12.0"]
```

No declarar SDK 8.0–8.11, SDK 6.x, versiones futuras ni rangos que no hayan sido probados. Si el portal de UltiMaker ofrece otra versión SDK más reciente, primero hay que comprobar su correspondencia oficial con Cura, adaptar el código y probarlo antes de cambiar esta declaración.

## Compatibilidad de código

- Usar PyQt6: `PyQt6.QtCore`, `PyQt6.QtGui` y `PyQt6.QtWidgets`.
- No reintroducir PyQt5 ni fallbacks a APIs Qt antiguas.
- Usar enums de Qt6, por ejemplo:
  - `Qt.AlignmentFlag.AlignCenter`.
  - `QAbstractItemView.SelectionBehavior.SelectRows`.
- Mantener el núcleo de análisis independiente de Cura y Qt.
- Mantener la UI separada de la lógica de dominio.
- El análisis debe ejecutarse en segundo plano y no bloquear Cura.
- Registrar la extensión mediante la API estándar de Cura (`Extension` y `register(app)`).
- No usar APIs privadas o internas de Cura salvo que exista una justificación documentada.
- No usar `Cura.API` por obligación: solo introducirlo si una función real del plugin lo necesita.

## Metadatos obligatorios

`plugin.json` debe tener los campos en la raíz, no dentro de un objeto `plugin`:

```json
{
  "name": "Cura Time Analyzer",
  "author": "Jorge Martín",
  "version": "X.Y.Z",
  "description": "...",
  "supported_sdk_versions": ["8.12.0"]
}
```

- Incrementar la versión cuando cambie código, compatibilidad o empaquetado publicado.
- Mantener `CHANGELOG.md` actualizado.
- No incluir tokens, contraseñas, claves API, URLs con credenciales ni datos de usuario.
- No afirmar soporte de una versión de SDK sin prueba real dentro de Cura.

## Estructura y empaquetado Marketplace

UltiMaker exige que el ZIP se cree desde una carpeta raíz cuyo nombre coincida con el Package ID:

```text
CuraTimeAnalyzer/
├── plugin.json
├── __init__.py
├── LICENSE
├── CHANGELOG.md
├── README.md
└── cura_time_analyzer/
```

El paquete runtime se genera siempre con:

```bash
python3 scripts/package_plugin.py
```

El nombre debe contener la versión:

```text
dist/CuraTimeAnalyzer-X.Y.Z.plugin
```

El archivo `.plugin` debe incluir solo runtime, licencia, README y changelog. No debe incluir:

- `.git/` o `.github/`.
- `tests/`.
- `docs/` de desarrollo.
- `scripts/`.
- `.pyc` o `__pycache__/`.
- Otros paquetes `.plugin` o `.zip`.
- Secretos o archivos `.env`.
- G-code, perfiles o datos reales del usuario.

El código fuente para el portal se entrega como ZIP separado:

```text
CuraTimeAnalyzer-X.Y.Z-source.zip
```

Debe contener la carpeta raíz `CuraTimeAnalyzer/`, el código fuente, tests, documentación, scripts, `LICENSE` y `CHANGELOG.md`, pero nunca `.git`, secretos ni paquetes generados.

Límite de Marketplace: **50 MB**.

## Requisitos de UltiMaker Marketplace

Antes de publicar, comprobar:

- El plugin no provoca crashes al instalarse, cargarse o desinstalarse.
- No depende de red para analizar G-code.
- No envía datos del usuario.
- Solo escribe en sus propias preferencias o en rutas elegidas por el usuario para exportación.
- Incluye licencia en la raíz del paquete.
- Incluye changelog cuando hay una actualización importante.
- No se actualiza por fuera de la infraestructura de paquetes de Cura.
- Todos los componentes incluidos tienen licencia compatible.
- El paquete pesa menos de 50 MB.
- El Package ID es estable y no contiene autor, versión ni tipo genérico en el nombre.

Documentación oficial:

- https://github.com/Ultimaker/Cura/wiki/SDK-Versions
- https://github.com/Ultimaker/Cura/wiki/plugin.json
- https://github.com/Ultimaker/Cura/wiki/Creating-Packages-Plugins-For-The-Marketplace
- https://contribute.ultimaker.com/

## Verificaciones obligatorias antes de cada release

Ejecutar desde la raíz del repositorio:

```bash
python3 -m pytest tests -q
python3 -m compileall -q cura_time_analyzer __init__.py scripts
python3 scripts/package_plugin.py
unzip -t dist/CuraTimeAnalyzer-<version>.plugin
python3 - <<'PY'
import json
from pathlib import Path
metadata = json.loads(Path("plugin.json").read_text())
assert metadata["supported_sdk_versions"] == ["8.12.0"]
print(metadata)
PY
git diff --check
```

También verificar manualmente:

1. El plugin carga en Cura 5.13.x.
2. Aparece `Extensions → Analizar tiempo por capa…`.
3. Se abre la ventana con PyQt6.
4. Se analiza un `.gcode` real en segundo plano.
5. Se analiza un `.gx` real.
6. Se muestra el heatmap.
7. JSON y CSV se exportan correctamente.
8. Cerrar la ventana no deja hilos activos.
9. Cura sigue funcionando después de analizar y exportar.
10. La instalación no modifica el G-code ni el perfil original.

Si no hay una instalación funcional de Cura 5.13.x disponible, indicar explícitamente que la verificación de carga/UI queda pendiente. Las pruebas unitarias y `compileall` no sustituyen la prueba real dentro de Cura.

## Instalación local Linux para pruebas

Para una instalación nativa de Cura 5.13.x:

```bash
rm -rf "$HOME/.local/share/cura/5.13/plugins/CuraTimeAnalyzer"
mkdir -p "$HOME/.local/share/cura/5.13/plugins"
unzip -q -o dist/CuraTimeAnalyzer-<version>.plugin \
  -d "$HOME/.local/share/cura/5.13/plugins"
```

Para Flatpak:

```bash
rm -rf "$HOME/.var/app/com.ultimaker.Cura/data/cura/5.13/plugins/CuraTimeAnalyzer"
mkdir -p "$HOME/.var/app/com.ultimaker.Cura/data/cura/5.13/plugins"
unzip -q -o dist/CuraTimeAnalyzer-<version>.plugin \
  -d "$HOME/.var/app/com.ultimaker.Cura/data/cura/5.13/plugins"
```

## Política de cambios

- No usar compatibilidad antigua para ocultar un fallo de la versión objetivo.
- No conservar SDK antiguos solo por ampliar artificialmente la lista del Marketplace.
- Si aparece un error de carga, leer primero el log de Cura y reproducirlo antes de cambiar metadatos al azar.
- Si una nueva versión de Cura cambia el SDK, crear una nueva versión del plugin y actualizar este archivo antes de publicar.
- Cada cambio publicado debe quedar en Git con un commit descriptivo y el árbol remoto verificado.
