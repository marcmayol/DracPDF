# lectorpdf

Visor de PDF de escritorio con rellenado de formularios, firma dibujada y firma
digital (PAdES). Escrito en Python con arquitectura hexagonal: el núcleo de
dominio no depende de Qt, PyMuPDF ni pyHanko.

## Requisitos

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) para gestión de dependencias

## Puesta en marcha

```bash
uv sync                 # instala dependencias (incluye grupo dev)
uv run lectorpdf        # arranca la aplicación
uv run pytest           # ejecuta los tests
uv run ruff check .     # lint
uv run mypy             # comprobación de tipos
```

Los PDF de prueba se generan con un script y no se versionan:

```bash
uv run python tests/adapters/generar_fixtures.py
```

## Arquitectura

```
src/lectorpdf/
  core/       # dominio, puertos y casos de uso (sin dependencias de infraestructura)
  adapters/   # implementaciones concretas (PyMuPDF, pyHanko)
  ui/         # interfaz PySide6
```

Consulta `PLAN.md` para el detalle de fases y criterios de aceptación.
