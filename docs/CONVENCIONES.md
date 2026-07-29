# Convenciones de trabajo

Este documento establece las convenciones iniciales del proyecto. Su propósito es dar consistencia al desarrollo documental y técnico sin introducir reglas que aún no hayan sido aprobadas por una decisión formal.

## 1. Idioma

- El código, los identificadores técnicos y los commits se escribirán en inglés.
- La documentación funcional y la interfaz se elaborarán inicialmente en español.
- Los nombres técnicos deberán preferir inglés para mantener consistencia con el stack previsto.

## 2. Nombres de archivos y carpetas

- Los archivos especiales de raíz pueden conservar nombres convencionales en mayúsculas, como README.md, AGENTS.md y CHANGELOG.md.
- Los archivos y carpetas de código seguirán la convención del lenguaje o framework correspondiente.
- Los nombres de archivos y carpetas deben ser descriptivos y evitar abreviaturas ambiguas.
- Los documentos de producto y de arquitectura deben mantenerse en la carpeta docs con una estructura simple y explícita.

## 3. Ramas de Git

- Se usarán ramas con prefijos claros, por ejemplo feature/, fix/, docs/, refactor/, test/ o chore/.
- Los nombres de rama usarán inglés y kebab-case después del prefijo, por ejemplo feature/workout-logging.
- Los nombres de rama deben ser cortos, descriptivos y estar relacionados con el cambio concreto.

## 4. Commits

- Los commits se escribirán con mensajes cortos y claros, preferiblemente siguiendo un estilo tipo Conventional Commits.
- Los mensajes deben explicar qué cambia y por qué, sin depender de contexto implícito.

## 5. Pull requests

- Cada pull request debe incluir un resumen del problema, los cambios, los criterios de aceptación, los riesgos y la documentación relacionada.
- No se deben mezclar cambios de producto, infraestructura y documentación sin justificación clara.

## 6. Nombres de entidades

- Los nombres de entidades del dominio se escribirán en inglés cuando se implementen en código.
- Los nombres de negocio visibles en la interfaz se mantendrán en español, salvo que exista una decisión posterior al respecto.

## 7. Endpoints

- Los endpoints deben usar nombres en inglés y seguir una estructura consistente por recurso.
- La API debe priorizar claridad y evitar redundancias innecesarias.
- Los endpoints deben reflejar el concepto de negocio y no mezclar responsabilidades.

## 8. Variables de entorno

- Las variables de entorno se escribirán en mayúsculas y con guiones bajos.
- No se introducirán variables nuevas sin una justificación documental y técnica.
- Los secretos no deben incluirse en el repositorio.

## 9. Migraciones

- Los cambios de esquema deben planificarse como migraciones y documentarse.
- No se asumirán migraciones ni cambios de base de datos sin un diseño previo y una justificación clara.

## 10. Fechas y horas

- Los timestamps se almacenarán en UTC.
- Las fechas de calendario sin hora, como birth_date, measurement_date o log_date, se almacenarán como fechas y no se convertirán a UTC.
- La interfaz mostrará fechas en la zona horaria del usuario.
- Los cálculos y agregaciones temporales deben documentar explícitamente la zona horaria que se aplica.

## 11. Unidades

- Las unidades internas iniciales serán:
  - masa: kilogramos;
  - longitud: centímetros;
  - duración: segundos;
  - energía alimentaria: kilocalorías;
  - líquidos: mililitros.
- La interfaz podrá convertir unidades según la preferencia del usuario.
- Las unidades internas deben normalizarse.
- Se debe evitar mezclar unidades de forma implícita en el modelo de datos o en los servicios.

## 12. Archivos de texto

- Los archivos de texto deberán utilizar UTF-8.
- No se convertirán en definitivas convenciones dependientes de una tecnología todavía no inicializada.

## 13. Estados

- Los estados de dominio deben ser claros, estables y usados de forma consistente.
- Se preferirá un conjunto limitado de estados frente a un modelo excesivamente fragmentado.
- Los estados deben documentarse para evitar ambigüedad entre borrador, activo, archivado, completado o cancelado.

## 14. Errores

- Los errores deben ser explícitos, trazables y comprensibles para el usuario y para el equipo.
- Los mensajes deben diferenciar entre error de validación, error de negocio, error de autorización y error técnico.

## 15. Pruebas

- Las pruebas deben cubrir el comportamiento real y relevante del sistema.
- No se introducirán convenciones de pruebas que dependan de herramientas no aprobadas aún.
- Las pruebas de lógica determinista deben basarse en entradas y resultados conocidos.

## 16. Documentación

- La documentación debe actualizarse cuando cambie el comportamiento observable del producto o la arquitectura.
- Los cambios técnicos importantes deben reflejarse en la documentación pertinente y, cuando sea necesario, en ADR.

## 17. Comentarios

- Los comentarios deben explicar el porqué de una decisión, no repetir lo obvio.
- No se introducirán comentarios excesivos en código que aún no exista.

## 18. Convenciones provisionales

- Estas convenciones son provisionales hasta que la arquitectura y la estructura técnica se formalicen.
- Cualquier convención que dependa de una tecnología aún no configurada debe considerarse pendiente de aprobación.
