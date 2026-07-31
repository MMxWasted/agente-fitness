# ADR-014 — Importación manual y versionada de mediciones desde XLSX

- Identificador: `ADR-014`
- Estado: `Accepted`

## Contexto

El historial corporal parte de un libro en el que cada columna de fecha
representa una revisión y las filas agrupan bioimpedancia, pliegues y
perímetros, incluidos valores bilaterales. El bloque 3B.2A debe ofrecer una
previsualización segura antes de diseñar la persistencia de 3B.2B.

El archivo contiene datos privados y OOXML es un contenedor ZIP con XML. No se
puede confiar en su extensión, MIME, estructura interna, fórmulas ni tamaños
declarados. Tampoco se debe ampliar `UserProfile` ni conservar el original.

No se proporcionó el libro personal al repositorio. El formato V1 se define
contra el fixture sintético y anonimizado
`backend/tests/fixtures/body_measurements/body_measurements_format_v1.xlsx`;
deberá contrastarse con una copia anonimizada del formato real antes de aceptar
variantes adicionales.

## Criterios de decisión

- Minimizar exposición y retención de datos corporales.
- Reconocer con precisión un formato conocido, no adivinar libros arbitrarios.
- Hacer visibles fechas, unidades y números ambiguos.
- Obtener una representación estable para la futura confirmación idempotente.
- Rechazar contenido que amplíe la superficie ZIP, XML o de fórmulas.
- Mantener parser, API, interfaz y futura persistencia separados.

## Decisión

### Flujo incremental

La primera entrada será una carga manual autenticada. 3B.2A lee el archivo,
reanuda sus valores en una previsualización y descarta el original al finalizar
la petición. No persiste fuente, importación, revisión ni valor.

3B.2B deberá volver a analizar el archivo durante la confirmación y comparar
el fingerprint normalizado con el mostrado. La previsualización no será una
entrada confiable para persistir y no se conservará el Excel original.

3B.2C queda reservado para consulta histórica, reversión y posibles
integraciones. OneDrive, analítica e integración con entrenamientos no forman
parte de 3B.2A.

### Adaptador específico

`BodyMeasurementWorkbookAdapterV1` acepta únicamente la hoja `Revisiones` con
las columnas `Categoría`, `Métrica`, `Unidad` y una o más columnas de revisión.
Reconoce secciones y alias controlados, propaga categorías combinadas,
normaliza lateralidad y usa `Decimal`. No es un importador universal ni admite
configuración arbitraria de usuarios.

Las etiquetas se normalizan con Unicode, mayúsculas, puntuación y espacios,
pero la respuesta conserva una etiqueta original acotada para revisión visual.
Las fórmulas nunca se ejecutan y una fórmula usada como etiqueta, unidad, fecha
o valor corporal bloquea el archivo.

### Catálogo V1

Todas las métricas tienen origen `reported`. Los rangos son controles básicos
de entrada, no umbrales médicos ni diagnósticos.

| Código | Categoría | Alias V1 principales | Unidad | Lado | Rango básico |
| --- | --- | --- | --- | --- | --- |
| `body_weight` | bioimpedance | peso corporal, peso | kg | ninguno | 0–500 |
| `body_mass_index_reported` | bioimpedance | índice de masa corporal, IMC, BMI | unitless_index | ninguno | 0–150 |
| `body_fat_percentage` | bioimpedance | grasa corporal, porcentaje de grasa | percent | ninguno | 0–100 |
| `body_water_percentage` | bioimpedance | agua corporal, porcentaje de agua | percent | ninguno | 0–100 |
| `muscle_mass` | bioimpedance | masa muscular | kg | ninguno | 0–500 |
| `physique_rating` | bioimpedance | valoración física, physique rating | unitless_level | ninguno | 0–20 |
| `bone_mass` | bioimpedance | masa ósea | kg | ninguno | 0–30 |
| `basal_metabolic_rate` | bioimpedance | metabolismo basal, tasa metabólica basal, BMR | kcal_per_day | ninguno | 0–10000 |
| `metabolic_age` | bioimpedance | edad metabólica | years | ninguno | 0–150 |
| `visceral_fat_level` | bioimpedance | grasa visceral, nivel de grasa visceral | unitless_level | ninguno | 0–100 |
| `quadriceps_skinfold` | skinfold | cuádriceps | mm | izquierdo/derecho | 0–150 |
| `triceps_skinfold` | skinfold | tríceps | mm | izquierdo/derecho | 0–150 |
| `subscapular_skinfold` | skinfold | subescapular, pliegue subescapular | mm | ninguno | 0–150 |
| `side_skinfold` | skinfold | costado, lateral | mm | izquierdo/derecho | 0–150 |
| `abdominal_skinfold` | skinfold | abdominal, abdomen | mm | ninguno | 0–150 |
| `waist_circumference` | circumference | cintura, perímetro de cintura | cm | ninguno | 0–400 |
| `hip_circumference` | circumference | cadera, perímetro de cadera | cm | ninguno | 0–400 |
| `shoulder_circumference` | circumference | hombros, perímetro de hombros | cm | ninguno | 0–400 |
| `chest_back_circumference` | circumference | pecho y espalda, tórax | cm | ninguno | 0–400 |
| `thigh_circumference` | circumference | muslo | cm | izquierdo/derecho | 0–250 |
| `arm_circumference` | circumference | brazo | cm | izquierdo/derecho | 0–150 |
| `flexed_arm_circumference` | circumference | brazo flexionado, brazo contraído | cm | izquierdo/derecho | 0–150 |

Las unidades aceptadas son `kg`, `cm`, `mm`, `percent`, `kcal_per_day`,
`years`, `unitless_index` y `unitless_level`. Su fuente queda marcada como
explícita en Excel, definición del adaptador o no resuelta. Una discrepancia no
se corrige silenciosamente.

### Fechas, números y lateralidad

Las fechas completas se validan y no pueden ser futuras. Un encabezado como
`06-03` solo produce el candidato día-mes; el año permanece sin resolver y
genera un error bloqueante. Si las fechas completas comparten un año se puede
mostrar como propuesta inferida, nunca como fecha confirmada.

Los números usan `Decimal`, aceptan coma o punto decimal, distinguen vacío de
cero y rechazan booleanos, NaN e infinitos. Un separador con posible lectura de
miles produce una advertencia. Los lados posibles son `none`, `left` y
`right`.

### Fingerprint

El fingerprint es SHA-256 de JSON canónico ordenado que incluye versión del
adaptador, identidad provisional de revisiones, fechas resueltas o
ambigüedades, métricas, lados, decimales canónicos, unidades, fuentes de unidad
y métricas desconocidas. Excluye nombre físico, propiedades, estilos y
posición de columnas cuando la identidad normalizada permite ordenarlas.

3B.2B deberá usarlo para detectar cambios entre previsualización y
confirmación, pero deberá recalcularlo desde el archivo recibido.

### Seguridad del contenedor

El backend limita inicialmente el archivo a 5 MiB y aplica antes del parseo:

- extensión `.xlsx` y MIME como señal auxiliar;
- firma ZIP y estructura OOXML mínima;
- número de entradas y tamaño total descomprimido;
- nombres únicos y rutas seguras;
- rechazo de cifrado, protección, macros y enlaces externos;
- rechazo de DTD y entidades XML;
- cierre del recurso de upload en `finally`.

Se adopta `openpyxl` 3.1.5, licencia MIT, para interpretar celdas, tipos, fechas
y rangos combinados. La biblioteca estándar cubre ZIP, pero no el modelo de
hoja OOXML completo. Se añade `defusedxml` 0.7.1 porque `openpyxl` recomienda
su uso frente a expansión de entidades y ataques XML; los límites ZIP propios
siguen siendo obligatorios. `pandas` no aporta valor a este parser acotado.

### Privacidad y errores

El propietario se resuelve exclusivamente desde el bearer; no existe
`user_id` en el contrato. La respuesta omite nombre de archivo, identidad
hallada, celdas arbitrarias, rutas temporales y tokens. Los errores son
genéricos y no registran contenido ni valores corporales.

## Contrato resultante

`POST /api/v1/body-measurement-imports/preview` recibe
`multipart/form-data`, exige bearer y devuelve 200 con adaptador, fingerprint,
metadatos técnicos seguros, revisiones, métricas, advertencias, errores,
desconocidos, celdas ignoradas y totales. Usa 401, 403, 413, 415 y 422 para los
errores documentados.

## Alternativas consideradas

- **Parser OOXML solo con biblioteca estándar:** reduce dependencias, pero
  obliga a reconstruir tipos, fechas, shared strings, estilos y combinaciones;
  se rechaza.
- **Pandas:** añade una superficie y abstracción tabular innecesarias; se
  rechaza.
- **Importador universal configurable:** oculta ambigüedades y amplía mucho la
  superficie de entrada; se rechaza.
- **Persistir el original:** facilita reanálisis, pero aumenta retención,
  seguridad y cumplimiento; se rechaza para este flujo.
- **Persistir directamente al cargar:** impide revisión previa y mezcla datos
  inseguros con el historial; se rechaza.

## Consecuencias

El flujo es verificable, privado y extensible por versión, y el frontend no se
acopla a posiciones de celda. A cambio, solo funciona con el formato V1 y una
fecha sin año no puede resolverse en esta entrega. La confirmación,
idempotencia persistente, versionado de revisiones, reversión y retención de
datos normalizados siguen pendientes de 3B.2B/3B.2C.

## Condiciones de revisión

Revisar el ADR al contrastar un formato real anonimizado, aceptar una nueva
plantilla, diseñar la persistencia, incorporar confirmación, sincronizar con
OneDrive o cambiar límites de seguridad. Cada formato nuevo debe tener versión,
fixture y pruebas propias.

## Documentos relacionados

- [ADR-002 — PostgreSQL](ADR-002-postgresql.md)
- [ADR-005 — Estrategia de autenticación](ADR-005-authentication-strategy.md)
- [ADR-007 — Preservación de datos históricos](ADR-007-historical-data-preservation.md)
- [Modelo de datos](../architecture/data-model.md)
- [Diseño de la API](../architecture/api-design.md)
- [Privacidad](../safety/privacy.md)
