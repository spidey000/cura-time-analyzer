# Cura Marketplace checklist

Este documento acompaña la solicitud de publicación; no se incluye en el paquete runtime.

- [x] `plugin.json` obligatorio en la raíz del plugin.
- [x] `name`, `author`, `version`, `description` y `supported_sdk_versions` en formato oficial.
- [x] `LICENSE` en la raíz del paquete.
- [x] `CHANGELOG.md` para releases y cambios importantes.
- [x] ZIP con carpeta raíz `CuraTimeAnalyzer/`.
- [x] Sin credenciales, `.env`, G-code del usuario ni datos privados.
- [x] Sin dependencias externas de red para el MVP.
- [x] Tamaño del paquete validado por el script de build.
- [ ] Validación de carga dentro de la versión exacta de Cura objetivo.
- [ ] Revisión final de compatibilidad Windows/macOS/Linux.
- [ ] Subida y revisión desde `https://contribute.ultimaker.com`.

La última lista requiere acciones en el portal y pruebas en instalaciones de Cura; no puede certificarse solo desde el entorno de desarrollo.
