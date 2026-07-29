# ADR-007 — Preservación de datos históricos

- Identificador: `ADR-007`
- Estado: `Accepted`

## Contexto

Las sesiones finalizadas son evidencia de actividad real. Si una edición posterior de rutina, ejercicio o regla de progreso altera retroactivamente esos datos, las métricas dejan de ser reproducibles y el usuario pierde confianza en el historial.

## Fuerzas o criterios de decisión

- Integridad y reproducibilidad histórica.
- Corrección explícita de errores reales.
- Trazabilidad de quién cambió qué y cuándo.
- Derechos de privacidad y minimización.
- Compatibilidad con cambios futuros del catálogo y las rutinas.

## Decisión

Los cambios posteriores no alterarán implícitamente sesiones históricas finalizadas. Se conservarán como invariantes el ejercicio planificado y realizado, las series y cargas relevantes, las sustituciones, los valores registrados y el contexto temporal.

Editar una rutina futura solo afectará planificación futura. Corregir un error histórico será una operación separada, explícita, autorizada y trazable. Borrar o anonimizar información por privacidad será un flujo distinto y podrá modificar o retirar datos conforme a la política aplicable, sin presentarse como una edición ordinaria del entrenamiento.

## Alternativas consideradas

- **Historial estable con correcciones explícitas:** protege reproducibilidad y permite rectificar errores de forma controlada.
- **Referencias vivas a la rutina actual:** reduce duplicación, pero reescribe el significado del pasado.
- **Inmutabilidad absoluta:** maximiza integridad, pero impediría correcciones legítimas y obligaciones de privacidad.

## Consecuencias positivas

- Las métricas pueden reconstruirse con datos coherentes.
- Los cambios de rutina no alteran sesiones terminadas.
- Las correcciones quedan diferenciadas y auditables.
- El usuario puede comprender por qué cambió un registro.

## Consecuencias negativas

- Se necesita almacenar contexto histórico suficiente.
- Las correcciones requieren flujos y permisos específicos.
- Exportación, anonimización y borrado serán operaciones más complejas.

## Riesgos

- Implementar relaciones en cascada que modifiquen el historial.
- Registrar auditoría excesiva o insuficiente.
- Usar correcciones para ocultar cambios sin trazabilidad.
- Mantener datos que deban eliminarse por una solicitud válida.

## Impacto en seguridad y privacidad

Solo el propietario autenticado y operaciones autorizadas podrán consultar o corregir registros. La trazabilidad deberá minimizar datos personales. Preservación histórica no significa retención ilimitada: exportación, eliminación, anonimización y backups se regirán por políticas específicas.

## Condiciones de revisión

Se revisará si una obligación de privacidad, una nueva política de retención o un cambio del dominio requiere ajustar qué contexto se conserva. Cualquier revisión deberá mantener la distinción entre edición futura, corrección explícita y tratamiento por privacidad.

## Documentos relacionados

- [Principios](../PRINCIPIOS.md)
- [Modelo de datos conceptual](../architecture/data-model.md)
- [ADR-006 — Versionado de rutinas](ADR-006-routine-versioning.md)
- [ADR-010 — Exportación y eliminación](ADR-010-data-export-deletion.md)

