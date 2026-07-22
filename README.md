<div align="center">

<img src="assets/brand/png/icon-256.png" alt="DracPDF" width="120" />

# DracPDF

**Lector de PDF de escritorio** — rellenado de formularios AcroForm, firma
dibujada a mano y firma digital con certificado (PAdES).

[![Descargar la última versión](https://img.shields.io/github/v/release/marcmayol/DracPDF?label=Descargar&style=for-the-badge&color=E0534A)](https://github.com/marcmayol/DracPDF/releases/latest)
&nbsp;
[![Windows](https://img.shields.io/badge/Windows-por%20usuario-2A2E37?style=for-the-badge&logo=windows)](https://github.com/marcmayol/DracPDF/releases/latest)
&nbsp;
[![Licencia](https://img.shields.io/badge/código%20visible%20·%20uso%20no%20comercial-6A7080?style=for-the-badge)](LICENSE)

</div>

---

Escrito en Python con **arquitectura hexagonal**: el núcleo de dominio no depende
de Qt, PyMuPDF ni pyHanko. Identidad visual "Ladón" (tema claro/oscuro
conmutable). El paquete interno se llama `lectorpdf` por razones históricas; la
aplicación es **DracPDF**.

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

## Licencia

**Copyright (c) 2026 Marc Mayol.** Código visible con **uso no comercial permitido**.

Puedes **usar, copiar, modificar y redistribuir** el Software con fines
**no comerciales**, conservando el aviso de licencia y la atribución. La
**explotación comercial** —directa o indirecta (venderlo, incluirlo en packs de
cursos o materiales de pago, distribuciones preinstaladas comerciales, bundles,
etc.)— queda **reservada al titular** y requiere su consentimiento previo y por
escrito. Detalle completo en [`LICENSE`](LICENSE).

Para una licencia comercial: marcmayolorell@gmail.com

> Nota: "código visible con uso no comercial" **no** es lo mismo que "código
> abierto" (open source), que no admite restricciones de uso comercial.
