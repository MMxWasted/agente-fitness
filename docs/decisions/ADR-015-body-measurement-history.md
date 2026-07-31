# ADR-015 — Persistencia, versionado y reversión del historial corporal

- Identificador: `ADR-015`
- Estado: `Accepted`

## Contexto

ADR-014 define la lectura segura y la previsualización de un XLSX conocido.
3B.2B debe confirmar esa interpretación, conservar observaciones normalizadas
y permitir reimportaciones y correcciones sin sobrescribir el pasado. Las
mediciones son privadas, el archivo no es una fuente permanente y una
confirmación puede competir con otra operación sobre la misma fuente.

## Criterios de decisión

- Propiedad derivada exclusivamente del usuario autenticado.
- Reanálisis obligatorio del archivo en planificación y confirmación.
- Idempotencia observable ante reintentos y contenido repetido.
- Historial inmutable con una sola versión vigente.
- Integridad reforzada mediante restricciones PostgreSQL.
- Reversión transaccional sin conservar el archivo original.
- Separación estricta respecto a `UserProfile` y a la futura analítica.

## Decisión

### Fuentes lógicas

`BodyMeasurementSource` representa un origen lógico privado. Su identidad es
un UUID y una `logical_key` inmutable y normalizada, única por usuario. El
`display_name` solo es presentación. `source_kind` empieza en `manual_excel`.
`history_version`, inicialmente cero y siempre no negativo, cambia tras cada
confirmación o reversión y permite rechazar planes obsoletos.

### Identidad y contenido

La identidad de una revisión es SHA-256 de una representación canónica del
propietario, fuente, fecha completa, etiqueta normalizada y disambiguador
normalizado. El hash de contenido es independiente y ordena por código,
categoría, lado, decimal canónico, unidad, origen y versión del catálogo.
Nombre del archivo, estilos, posiciones visuales, propiedades del libro y
etiquetas cosméticas no participan en esos hashes.

Una identidad nueva crea una revisión. La misma identidad y contenido se
omite. La misma identidad con contenido distinto exige `create_version`; el
rechazo es la acción predeterminada.

### Versionado inmutable

Cada versión conserva sus propios valores `NUMERIC(14,6)`. Una modificación
crea otra fila, enlaza `supersedes_review_id`, incrementa el número de versión
y cambia la versión vigente. Un índice parcial garantiza como máximo una fila
vigente por fuente e identidad. La unicidad del predecesor evita bifurcaciones.
Los valores históricos nunca se actualizan en sitio.

### Planificación y confirmación

Planificación y confirmación reciben el mismo archivo y solo decisiones
estructurales: fechas, aceptación acotada de unidad canónica, exclusiones,
disambiguadores y acción ante modificaciones. No reciben valores corporales,
identidades ni hashes del cliente como autoridad.

Ambas operaciones vuelven a ejecutar `BodyMeasurementWorkbookAdapterV1` y
comparan el fingerprint de previsualización. La planificación no persiste
mediciones y devuelve clasificación, `history_version` y un fingerprint
confirmado. La confirmación repite el análisis, bloquea la fuente mediante
`SELECT ... FOR UPDATE`, verifica la versión y persiste en una sola transacción.

### Idempotencia HTTP y concurrencia

La confirmación exige una `Idempotency-Key` acotada. Solo se almacena su
SHA-256, junto con un digest canónico de archivo, fuente, fingerprints,
versión y decisiones. La misma clave y digest reproduce el resultado; la misma
clave con otro digest devuelve 409. La clave no identifica revisiones.

El bloqueo por fuente serializa confirmaciones, versionados y reversiones. Las
restricciones de unicidad y el índice parcial actúan como defensa adicional.

### Reversión

Una importación propia puede marcarse `reverted` en una transacción. Se
eliminan físicamente sus valores y revisiones, se restaura el predecesor cuando
existe y se incrementa `history_version`. La fila de importación conserva solo
auditoría técnica, contadores y timestamps. Una versión posterior dependiente
bloquea la operación con 409. No existe reversión parcial.

### Retención y privacidad

El XLSX, su nombre y rutas temporales no se conservan. Hashes, valores,
fechas, etiquetas y decisiones completas no se escriben en logs ni se exponen
en listados de importación. Las revisiones privadas permanecen hasta una
reversión explícita o la eliminación futura de la cuenta. La política general
de backups y retención continúa bajo ADR-010.

### Límite del bloque

Las cuatro entidades son independientes de `UserProfile`. 3B.2B ofrece
persistencia e historial factual. Series, comparaciones, gráficos y analítica
corporal determinista pertenecen a 3B.2C.

## Alternativas consideradas

- **Sobrescribir una revisión:** simplifica el esquema, pero destruye evidencia
  histórica; se rechaza.
- **Usar el hash del archivo como identidad:** confunde contenedor y revisión
  y no detecta correctamente columnas; se rechaza.
- **Guardar valores como JSON:** debilita tipos, restricciones y consultas; se
  rechaza.
- **Persistir la previsualización enviada por el cliente:** permite manipular
  valores; se rechaza.
- **Conservar el XLSX:** facilita reanálisis, pero aumenta retención y riesgo;
  se rechaza.
- **Bloqueo global:** evita carreras, pero reduce concurrencia innecesariamente;
  se adopta bloqueo por fuente.

## Consecuencias

La confirmación es reproducible, privada y resistente a reintentos y carreras.
El coste es un modelo relacional mayor, reenvío del archivo y reglas estrictas
de versión y reversión. El navegador debe conservar temporalmente el `File` y
la clave de idempotencia mientras dure el flujo activo.

## Riesgos

- Un bloqueo demasiado largo puede degradar importaciones concurrentes.
- Una normalización inestable puede crear identidades distintas.
- Una precisión decimal no validada podría redondearse en PostgreSQL.
- Una reversión sin comprobar descendientes podría romper una cadena.
- Logs o errores descuidados podrían revelar información corporal.

Estos riesgos se mitigan con parseo previo al bloqueo, hashes canónicos
versionados, validación de escala, restricciones, transacciones y pruebas sobre
PostgreSQL real.

## Condiciones de revisión

Revisar si se incorpora otra fuente, sincronización automática, edición manual,
retención regulada, varias ramas de corrección o referencias persistentes desde
3B.2C. Una decisión incompatible requerirá otro ADR.

## Documentos relacionados

- [ADR-002 — PostgreSQL](ADR-002-postgresql.md)
- [ADR-007 — Preservación de datos históricos](ADR-007-historical-data-preservation.md)
- [ADR-010 — Exportación y eliminación](ADR-010-data-export-deletion.md)
- [ADR-014 — Importación XLSX](ADR-014-body-measurement-xlsx-import.md)
- [Modelo de datos](../architecture/data-model.md)
- [Diseño de la API](../architecture/api-design.md)
- [Privacidad](../safety/privacy.md)
