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

### Fase 7: Conversiones de formato

Restricción global: todo llega por pip y viaja dentro del instalador; prohibido detectar o invocar programas del sistema (Word, LibreOffice). El motor de composición para Word→PDF es el propio Qt. Esta fase nace bajo las "Reglas de aceptación de UI" del plan: incluye su tabla declarativa de acciones y amplía el test de inventario.

#### Parte A: conversiones salientes (PDF → otros formatos)
1. Puerto ConversorPDF en el core, con casos de uso ConvertirAWord, ConvertirAHtml, ConvertirAMarkdown; pdf2docx queda aislada detrás de su propio adaptador (es la dependencia con más riesgo de mantenimiento futuro: su cirugía debe ser local).
2. PDF → Word con pdf2docx: rango de páginas elegible; al añadir la dependencia, verificar que NO hace downgrade del PyMuPDF del proyecto (si hay conflicto de versiones, se fija la nuestra y se prueba; no se acepta la suya sin más).
3. PDF → HTML con fitz (get_text("html")), documento completo o rango, con las imágenes embebidas o en carpeta aneja (elegible).
4. PDF → Markdown con fitz: extracción por bloques posicionales con heurística de títulos (tamaño de fuente relativa) y tablas básicas; el resultado prioriza texto limpio para edición/LLMs sobre réplica visual.
5. Los PDFs escaneados (sin capa de texto) se detectan y avisan: la conversión saldría vacía o como imagen; no se promete OCR en esta fase.

#### Parte B: conversión entrante (Word → PDF, "reformateado")
6. Word → PDF por la cadena mammoth → HTML → QTextDocument → QPdfWriter: texto real seleccionable, tablas, listas, negritas/cursivas e imágenes del docx; tamaño de página y márgenes configurables en el diálogo.
7. Etiquetado honesto en la UI: la acción se llama "Convertir Word a PDF (reformateado)..." y el diálogo aclara que conserva contenido y estructura, no el diseño exacto del original.

#### Integración en UI (según la estructura de menús vigente; "Herramientas" ya no existe)
8. Las conversiones salientes van en Documento → Convertir (submenú: A Word..., A HTML..., A Markdown...), operando sobre el documento abierto, con el worker de progreso y cancelación existente; deshabilitadas sin documento abierto.
9. Word → PDF va en Archivo → "Convertir Word a PDF..." (no opera sobre el documento abierto: pide un .docx externo); al terminar ofrece abrir el PDF resultante.
10. Tabla de acciones de la fase declarada en el test de inventario: las cuatro acciones con su menú de destino y condición de habilitación.

#### Reglas propias de esta fase
- El adaptador de Word→PDF (usa Qt) vive fuera del core: el caso de uso recibe el puerto como cualquier otro.
- Salidas atómicas (temporal + replace), como todo lo que escribe fichero.
- Fixtures por script: un docx de prueba generado con python-docx (títulos, tabla, lista, imagen, negritas) y un PDF multipágina con títulos y tabla para las salientes.
- Documentos FIRMADOS: las conversiones salientes SÍ se permiten (leen, no modifican el original).

**Criterio de aceptación:** (funcional) script de verificación sin UI que: convierte un PDF de fixture a docx comprobando texto y al menos una tabla; a HTML y Markdown comprobando texto y títulos; convierte el docx de fixture a PDF comprobando con fitz texto presente, tabla renderizada y texto seleccionable; y detecta un PDF escaneado avisando; todo con exit 0 y pip sin downgrade de PyMuPDF. (UI) el test de inventario ampliado pasa: las tres acciones de Documento → Convertir y la de Archivo existen, están conectadas, habilitadas/deshabilitadas según su condición, y la evidencia parte de las acciones, no de métodos privados.

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

### Fase 9: Texto y anotaciones

Añadir contenido textual al PDF y corregir texto existente de forma acotada y honesta. Nace bajo las Reglas de aceptación de UI (tabla de acciones + inventario). Documentos FIRMADOS: todas las operaciones de esta fase se rechazan con la salida ya existente de "guardar una copia editable".

#### Parte A: añadir texto y anotaciones
1. Caso de uso `AñadirTexto`: estampa un texto en un rectángulo de una página (fuente de una lista embebida, tamaño, color); reutiliza el patrón del modo de colocación de la firma (dibujar rectángulo, escribir, mover/redimensionar antes de confirmar). Marca cambios sin guardar en el registro
2. Anotaciones de marcado sobre la selección de texto existente (Fase 8): resaltar, subrayar y tachar, con color elegible entre los tokens semánticos; se crean como anotaciones estándar del PDF (visibles en cualquier visor) y se pueden eliminar (clic derecho sobre la anotación → eliminar)
3. Nota adhesiva: anotación de texto emergente colocable en la página, editable y eliminable
4. Integración: menú Edición (Añadir texto…, y las anotaciones también en el menú contextual de la selección) y grupo en la toolbar SOLO si la maqueta lo prevé; deshacer/rehacer de la Fase 8 cubre estas operaciones
5. Las anotaciones y textos añadidos se ven en el render inmediatamente (invalidación de caché de la página afectada) y sobreviven a guardar/reabrir

#### Parte B: corregir texto existente (acotada)
6. Caso de uso `CorregirTexto`: dado un tramo seleccionado de una línea, lo elimina por redacción y escribe el texto de sustitución en su posición con tamaño equivalente y fuente sustituta de la lista embebida. Acción "Corregir texto…" (doble clic sobre texto o menú Edición): diálogo con el texto original, el campo de sustitución y el aviso de límites (fuente sustituta puede diferir de la original; sin reflujo: la corrección no reajusta el párrafo)
7. Límites duros que el diálogo comunica y el código impone: tramos dentro de una sola línea; si el texto nuevo no cabe en el ancho disponible con el tamaño original, se ofrece reducir tamaño o cancelar, nunca invadir el texto vecino
8. Si al probar con PDFs reales la calidad de la sustitución de fuente resulta inaceptable de forma general (no en casos raros), la Parte B se recorta a lo que funcione dignamente y se documenta el recorte en PLAN.md; el recorte se decide con el titular, no unilateralmente

#### Parte C: imágenes (quitar y añadir)
9. Caso de uso `AñadirImagen`: inserta una imagen desde fichero (PNG/JPEG) en un rectángulo de la página, con el mismo modo de colocación de la Parte A (mover/redimensionar antes de confirmar, conservando proporción por defecto)
10. Caso de uso `EliminarImagen`: modo "seleccionar imagen" en el que las imágenes de la página se detectan (`get_image_rects`) y se resaltan al pasar el ratón; clic selecciona mostrando el contorno EXACTO de lo que se eliminará, y confirmar la elimina del documento (`delete_image`). Si la imagen aparece en más páginas o su rect cubre la página entera (escaneo), el diálogo de confirmación lo avisa antes
11. Integración: menú Edición (Añadir imagen…, Eliminar imagen…) y contextual de página; deshacer cubre ambas; render invalidado y cambios marcados como el resto de la fase

#### Reglas propias de esta fase
- Fuentes embebidas en la app para el texto nuevo: una serif, una sans y una mono con licencia libre (OFL), empaquetadas en `assets/fonts/` y registradas en PyMuPDF; nada de depender de fuentes del sistema (el PDF debe verse igual en cualquier máquina)
- Fixtures por script: PDF con párrafos y tamaños variados para corrección, y uno con texto seleccionable multibloques para anotaciones
- La redacción de la Parte B elimina de verdad el texto original del contenido (no lo tapa): verificado extrayendo el texto tras corregir

**Criterio de aceptación (definición de "hecho"):** añadir texto con fuentes embebidas, resaltar, subrayar, tachar y notas funcionan sobre el documento y sobreviven a guardar/reabrir; añadir y eliminar imágenes funcionan y sobreviven a reabrir; y la corrección de texto existente funciona dentro de sus límites declarados (una línea, sin invadir vecinos, texto original realmente eliminado) O BIEN se ha recortado con la aprobación explícita del titular mostrada en la conversación y el recorte está documentado en PLAN.md. Se muestra la salida de pytest con todos los tests en verde incluido el inventario de acciones ampliado (acciones nuevas con destino y condición, deshabilitadas con documento firmado, evidencia desde las acciones y deshacer demostrado desde el menú), la salida del script de verificación funcional (texto añadido persistente con fuente embebida; anotaciones estándar creadas y una eliminada; imagen añadida y otra eliminada verificadas tras reabrir; texto corregido con el original no extraíble y el caso "no cabe" ofreciendo alternativas) con exit 0, y git log con un commit por tarea.

## Reglas para la implementación
- El core no puede importar PySide6 ni PyMuPDF ni pyHanko; solo los adaptadores
- Cada caso de uso con test unitario usando fakes de los puertos
- Type hints estrictos, mypy en CI local
- Generar PDFs de fixture con script (no binarios a mano en el repo)
- Commits por tarea, no por fase

## Fuera de alcance (v1)
- Edición de texto del PDF con reflujo del párrafo (la Fase 9 permite solo corrección acotada de un tramo de una línea, sin reajustar el párrafo)
- XFA
- OCR

(Anotaciones de marcado y notas, y la corrección acotada de texto, pasan a estar en alcance en la **Fase 9**.)
