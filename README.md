# DracPDF

Visor de PDF de escritorio con rellenado de formularios AcroForm, firma dibujada
a mano y firma digital con certificado (PAdES). Escrito en Python con
arquitectura hexagonal: el núcleo de dominio no depende de Qt, PyMuPDF ni pyHanko.

Identidad visual "Ladón" (tema claro/oscuro conmutable). El paquete interno se
llama `lectorpdf` por razones históricas; la aplicación es **DracPDF**.

## Descargar (Windows)

**➡️ [Descargar la última versión](https://github.com/marcmayol/DracPDF/releases/latest)**

En esa página, descarga el instalador `DracPDF-<versión>-setup.exe` y ejecútalo.
La instalación es **por usuario** (no requiere permisos de administrador): crea el
acceso directo en el menú Inicio y la asociación con archivos PDF. Para
actualizar, ejecuta encima el instalador de la versión nueva.

## Requisitos

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) para gestión de dependencias

## Puesta en marcha

```bash
uv sync                 # instala dependencias (incluye grupo dev)
uv run lectorpdf        # arranca la aplicación (DracPDF)
uv run pytest           # ejecuta los tests
uv run ruff check .     # lint
uv run mypy             # comprobación de tipos
```

## Empaquetado (Windows)

```bash
uv run python scripts/generar_certificado.py   # certificado PKCS#12 de prueba
uv run python scripts/construir_exe.py         # dist/DracPDF.exe (PyInstaller)
uv run python scripts/construir_instalador.py  # dist/installer/DracPDF-*-setup.exe (Inno Setup)
```

## Arquitectura

```
src/lectorpdf/
  core/       # dominio, puertos y casos de uso (sin dependencias de infraestructura)
  adapters/   # implementaciones concretas (PyMuPDF, pyHanko)
  ui/         # interfaz PySide6 (tema "Ladón")
```

Consulta `PLAN.md` para el detalle de fases y criterios de aceptación.

## Licencia y propiedad

**Copyright (c) 2026 Marc Mayol. Todos los derechos reservados.**

Software propietario de código visible: el código se publica solo para consulta.
No se permite su uso, copia, modificación ni distribución, ni la explotación
comercial directa o indirecta (incluir en packs de cursos, distribuciones
preinstaladas, bundles, etc.), sin el consentimiento previo y por escrito del
titular. Consulta el fichero [`LICENSE`](LICENSE). Para solicitar autorización:
marcmayolorell@gmail.com.
