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

### Fase 5: Identidad visual (diseño "Ladón")

Fuente de verdad del diseño: proyecto de Claude Design "Identidad Ladón.dc.html".
Importar vía MCP de claude_design (https://api.anthropic.com/v1/design/mcp, auth con /design-login):
https://claude.ai/design/p/12145c22-8a62-4f15-bcb7-41d3448492c9?file=Identidad+Lad%C3%B3n.dc.html

1. Importar el diseño con el MCP y extraer los tokens (colores, tipografía, espaciados, radios, estados de firma) a `src/lectorpdf/ui/theme/tokens.py`: un dataclass por tema (claro/oscuro), sin valores sueltos por el código
2. Generar el QSS desde los tokens (plantilla + render en arranque o script de build), con conmutador de tema claro/oscuro en la UI y persistencia de la elección en la configuración
3. Assets del logo: guardar los assets de marca FUENTE del diseño en `assets/brand/` (los SVG de iconos son texto y se versionan siempre; el logo del diseño es PNG ráster afinado a mano por tamaño, y por ser FUENTE —sin él no se reconstruye el icono— también se versiona); script `scripts/generar_iconos.py` que genera desde ellos el .ico multiresolución (16/32/48/256) y los PNG para Linux; los artefactos DERIVADOS por el script (.ico, PNG redimensionados) NO se versionan
4. Iconografía de toolbar: SVG monocromos recoloreados por tema (abrir, guardar, zoom, navegación, dibujar firma, firmar con certificado, verificar), reemplazando los iconos actuales
5. Aplicar la identidad: icono de ventana y ejecutable, título de la app, pantalla "acerca de" con el logo; renombrado del binario a "ladon" SOLO si lo confirmo cuando llegue la tarea
6. Revisión pantalla a pantalla contra las maquetas del diseño: vista principal, modo formulario, diálogo de firma dibujada y panel de verificación con sus tres estados; ajustar QSS hasta la correspondencia razonable

#### Reglas propias de esta fase
- Ningún color/medida hardcodeado fuera de tokens.py
- El QSS no debe romper el overlay de formularios ni el canvas de firma (test de humo de cada pantalla tras aplicar tema)
- Los estados de firma usan los tokens semánticos del diseño (no verde/rojo/ámbar puros)

**Criterio de aceptación:** la app arranca con tema claro y oscuro conmutables y persistentes, toda la UI usa tokens, `generar_iconos.py` produce el .ico y los PNG desde los SVG con exit 0, y las cuatro pantallas clave se corresponden con las maquetas.

### Fase 6: Herramientas de PDF

Operaciones de manipulación de PDF integradas en un menú "Herramientas" y en el panel de miniaturas. (Reconstruida a partir del criterio de aceptación acordado.)

1. **Unir**: combinar varios PDF en uno nuevo. Opera sobre RUTAS de ficheros cerrados (el usuario elige N ficheros → PDF nuevo). El documento abierto puede prerrellenarse como primer elemento, pero se une desde su fichero en disco. Si un fichero elegido está abierto con cambios sin guardar, avisar y ofrecer guardarlo antes de unir.
2. **Organizar páginas**: reordenar, rotar y eliminar páginas del documento abierto desde el panel de miniaturas, con invalidación de la caché de render y refresco de miniaturas.
3. **Dividir**: separar un PDF (por páginas o por rangos) en varios ficheros.
4. **Proteger**: cifrar con contraseña.
5. **Desproteger**: quitar la contraseña (reabrir sin cifrado, con igualdad de contenido verificable).
6. **Comprimir**: reducir el tamaño del fichero, reportando la reducción.
7. **Exportar**: a PNG (una imagen por página) y a texto.

#### Reglas propias de esta fase
- Unir opera sobre rutas de ficheros cerrados, no sobre documentos del registro.
- El core sigue síncrono y sin Qt: los casos de uso son funciones síncronas; la concurrencia vive solo en la UI (QThread/QRunnable que invoca el caso de uso y emite progreso/cancelación). Un caso de uso que reporte progreso recibe un `Callable` simple del dominio, no señales Qt.
- Las operaciones que mutan el documento abierto se rechazan si está FIRMADO (coherencia con las marcas del registro).

**Criterio de aceptación:** script que une (con el orden comprobado), divide, protege y reabre con contraseña, desprotege (con igualdad verificada), comprime (con la reducción reportada) y exporta a PNG y texto, con exit 0; y demostración de que las operaciones sobre un documento FIRMADO se rechazan.

### Fase 8: Fundamentos de visor

Fuente de verdad visual: extensión del diseño "Identidad Ladón" para menús y navegación (Claude Design; se facilitará la URL de importación al inicio). Todo componente nuevo usa sus tokens; nada de estilo Qt por defecto.

#### Parte 0: estilo
1. Importar la extensión del diseño vía MCP de claude_design, ampliar tokens.py y el QSS generado con los componentes nuevos (menús, barra de búsqueda, árbol de outline, diálogos); test de humo de ambos temas

#### Parte A: navegar y usar el documento
2. Buscar en el documento (Ctrl+F): barra según diseño, búsqueda con search_for por página, resaltado de resultados sobre el render (resultado activo destacado vs. resto), contador "n de m", navegación F3/Shift+F3, coincidir mayúsculas; la búsqueda en documentos grandes no bloquea la UI (worker de la Fase 6)
3. Seleccionar y copiar texto: selección por arrastre sobre los rects de texto de fitz, resaltado visual, Ctrl+C al portapapeles; doble clic selecciona palabra, triple clic párrafo
4. Índice del documento: panel con get_toc() como árbol (pestaña junto a miniaturas, según diseño), clic navega, se oculta si el PDF no trae outline
5. Ir a página (Ctrl+G) con diálogo según diseño, y enlaces del PDF clicables: internos navegan, externos abren en el navegador tras confirmación
6. Imprimir (Ctrl+P): QPrintDialog + render a la resolución de la impresora, con rango de páginas; vista previa si QPrintPreviewDialog encaja con el tema sin pelearse
7. Modos de vista persistentes: ajuste a ancho/página, doble página, pantalla completa (F11), rotación de vista (no modifica el fichero)

#### Parte B: básicos de aplicación
8. Menú Archivo completo: abrir recientes (QSettings, rutas elididas según diseño, limpiar lista), guardar como/guardar copia (esta última es también la salida ofrecida por el aviso de documento firmado)
9. Restaurar estado: última página y zoom por documento (QSettings, clave por ruta), y opción de reabrir los documentos de la sesión anterior
10. Instancia única: QLocalServer/QLocalSocket; abrir un PDF desde el explorador con la app ya abierta lo carga en la instancia existente y trae la ventana al frente
11. Deshacer/rehacer en formularios (Ctrl+Z/Ctrl+Y): historial de valores por documento; deshacer restaura el valor anterior en el doc y en el widget visible
12. Propiedades del documento (diálogo según diseño): metadatos, versión PDF, cifrado, nº de páginas, tamaño de fichero
13. Repaso de atajos y menú contextual de página (según diseño) con las acciones aplicables

#### Reglas propias de esta fase
- Buscar/seleccionar operan sobre coordenadas de fitz transformadas con el mismo mapeo página→escena de los formularios: reutilizar, no duplicar
- El historial de deshacer vive junto al documento en el registro y se limpia al cerrar (misma disciplina que las marcas)
- Nada de esta fase modifica el documento salvo formularios ya existentes (deshacer incluido); la rotación de vista y los modos son presentación pura
- La instancia única no debe romper el flujo de tests (activable por flag, desactivada en tests)

**Criterio de aceptación:** con un PDF de fixture con outline, enlaces y texto: la búsqueda de un término reporta las ocurrencias correctas y navega entre ellas; la selección de un rango conocido copia exactamente ese texto; el outline del panel coincide con get_toc(); imprimir a un QPrinter de PDF virtual produce el nº de páginas del rango pedido; recientes, última página y zoom persisten tras cerrar y reabrir; una segunda invocación de la app con otro PDF llega a la instancia existente; y deshacer tras editar dos campos restaura los valores en orden. Demostrado por script/tests con exit 0.

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
