# ADR-010 — Exportación y eliminación de datos

- Identificador: `ADR-010`
- Estado: `Accepted`

## Contexto

El usuario debe poder controlar sus datos personales y de actividad. Exportar y eliminar no son una única operación: cada una afecta formatos, relaciones históricas, trazabilidad, retención técnica y copias de seguridad de manera diferente. La capacidad está aceptada, aunque sus plazos y mecanismos todavía no estén implementados.

## Fuerzas o criterios de decisión

- Control y comprensión por parte del usuario.
- Cobertura de datos y relaciones.
- Autenticación y confirmación reforzada.
- Integridad, privacidad y minimización.
- Retención técnica y recuperación.
- Formatos comprensibles y portables.

## Decisión

El producto ofrecerá mecanismos explícitos de exportación y eliminación. La exportación producirá una representación comprensible de los datos del usuario y deberá informar alcance y estado.

La eliminación distinguirá entre desaparición visible, borrado lógico, borrado físico y anonimización. La retención técnica y las copias de seguridad se tratarán por separado, con políticas observables. No se fijan en este ADR plazos de retención ni se afirma cumplimiento normativo.

## Alternativas consideradas

- **Exportación y eliminación como capacidades de producto:** ofrece control, pero exige flujos transaccionales y documentación.
- **Gestión manual por soporte:** reduce desarrollo inicial, pero es menos observable y escalable.
- **Solo borrado lógico:** facilita recuperación, pero no satisface por sí solo la eliminación física o anonimización.
- **Borrado físico inmediato en todos los sistemas:** minimiza persistencia, pero puede ser inviable para backups y recuperación segura.
- **Anonimización:** puede preservar estadísticas, siempre que sea irreversible y esté justificada.

## Consecuencias positivas

- El usuario dispone de mecanismos comprensibles de control.
- Las categorías de eliminación quedan diferenciadas.
- Backups y retención técnica no se ocultan bajo una etiqueta genérica.

## Consecuencias negativas

- La implementación atravesará múltiples entidades y almacenes.
- La exportación necesita versionado de formato y manejo de volumen.
- El borrado puede entrar en tensión con integridad histórica, auditoría y recuperación.

## Riesgos

- Exportaciones incompletas o entregadas a una identidad incorrecta.
- Eliminar parcialmente datos relacionados.
- Presentar borrado lógico como eliminación definitiva.
- Conservar copias sin política o anonimización reversible.

## Impacto en seguridad y privacidad

Ambas operaciones requerirán usuario autenticado, autorización, confirmación explícita y trazabilidad mínima. La entrega deberá protegerse frente a accesos ajenos. Los procesos evitarán incluir secretos, datos de otros usuarios o razonamiento interno del agente.

## Condiciones de revisión

Se revisará al definir políticas de retención, backups, restauración y formatos; al incorporar proveedores externos; o si una revisión especializada identifica obligaciones adicionales. Los plazos concretos deberán formalizarse en otra decisión o política.

## Documentos relacionados

- [Privacidad](../safety/privacy.md)
- [Historias de usuario](../product/user-stories.md)
- [ADR-007 — Preservación histórica](ADR-007-historical-data-preservation.md)
- [ADR-009 — Almacenamiento de conversaciones](ADR-009-conversation-storage.md)

