# Visor de PDF con firma y rellenado de formularios

## Objetivo
Aplicación de escritorio en Python: visor de PDF que permite rellenar formularios AcroForm, estampar una firma dibujada a mano y firmar digitalmente con certificado (PAdES).

## Stack
- Python 3.12+
- PySide6 (UI)
- PyMuPDF (renderizado, formularios, estampado de imágenes)
- pyHanko (firma digital PAdES, PKCS#12, TSA)
- pytest para tests
- Gestión de dependencias con uv

## Arquitectura
Hexagonal / puertos y adaptadores. El core no importa nada de Qt.

```
src/
  core/
    domain/          # Documento, Pagina, CampoFormulario, Firma
    ports/           # DocumentRepository, SignatureService, FormService
    use_cases/       # AbrirDocumento, RellenarCampo, EstamparFirma, FirmarDigitalmente
  adapters/
    pymupdf/         # Implementación de DocumentRepository y FormService
    pyhanko/         # Implementación de SignatureService
  ui/
    main_window.py
    viewer/          # Widget de renderizado de páginas
    forms/           # Overlay de widgets sobre campos
    signature/       # Canvas de dibujo + diálogo de firma digital
tests/
  core/              # Tests de casos de uso con fakes
  adapters/          # Tests de integración con PDFs de fixture
```

## Fases

### Fase 1: Visor básico
1. Esqueleto del proyecto (uv, estructura de carpetas, pre-commit con ruff)
2. Caso de uso `AbrirDocumento` + adaptador PyMuPDF
3. `ViewerWidget` con QGraphicsView: renderiza páginas como QImage
4. Renderizado perezoso: solo páginas visibles ± 1, con caché LRU
5. Zoom (Ctrl+rueda, botones, ajustar a ancho/página), navegación, panel de miniaturas
6. Abrir por diálogo y por drag & drop

**Criterio de aceptación:** abre un PDF de 500+ páginas sin bloquear la UI; scroll y zoom fluidos.

### Fase 2: Formularios
1. `FormService.listar_campos()` sobre `page.widgets()` de PyMuPDF: texto, checkbox, radio, combo, listbox
2. Overlay de widgets Qt posicionados sobre las coordenadas de cada campo (transformar coords PDF → coords vista según zoom)
3. Escritura de valores: `widget.field_value` + `widget.update()`; guardado con `doc.save()` incremental
4. Detección de XFA: si el PDF es XFA, mostrar aviso de no soportado
5. Tests con PDFs de fixture que incluyan cada tipo de campo

**Criterio de aceptación:** rellenar un formulario oficial (tipo modelo de hacienda con AcroForm), guardar y que los valores se vean en otro visor.

### Fase 3: Firma dibujada
1. `SignatureCanvas`: QWidget con QPainterPath, captura ratón/stylus, trazo suavizado, fondo transparente
2. Exportar a PNG con transparencia
3. Modo "colocar firma": el usuario dibuja un rectángulo sobre la página y se estampa con `page.insert_image()`
4. Biblioteca de firmas guardadas (carpeta de configuración del usuario, ~/.config/nombre-app/)
5. Poder redimensionar/mover la firma antes de confirmar

**Criterio de aceptación:** firma estampada visible en Adobe Reader, con transparencia correcta.

### Fase 4: Firma digital (PAdES)
1. `SignatureService` con pyHanko: cargar certificado PKCS#12 (.p12/.pfx) con contraseña
2. Firma con sello visible: posición elegida por el usuario, con nombre del firmante y fecha
3. Sellado de tiempo (TSA) opcional configurable
4. Verificación de firmas existentes en el documento: mostrar estado (válida/inválida/desconocida) en un panel
5. Orden de guardado: cualquier modificación (formularios, estampado) se aplica ANTES de la firma criptográfica; tras firmar, bloquear edición o forzar nueva revisión incremental
6. Opcional: soporte PKCS#11 para tokens hardware (DNIe, FNMT)

**Criterio de aceptación:** el PDF firmado valida en verde en Adobe Reader (certificado de prueba autofirmado añadido a confianza) y la verificación detecta manipulación posterior.

## Reglas para la implementación
- El core no puede importar PySide6 ni PyMuPDF ni pyHanko; solo los adaptadores
- Cada caso de uso con test unitario usando fakes de los puertos
- Type hints estrictos, mypy en CI local
- Generar PDFs de fixture con script (no binarios a mano en el repo)
- Commits por tarea, no por fase

## Fuera de alcance (v1)
- Edición de texto del PDF
- Anotaciones (subrayado, comentarios)
- XFA
- OCR
