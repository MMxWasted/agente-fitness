# ADR-008 — Confirmaciones para acciones sensibles del agente

- Identificador: `ADR-008`
- Estado: `Accepted`

## Contexto

El Agente Fitness puede consultar datos y producir propuestas, pero una respuesta del modelo no constituye autorización. Aplicar cambios sensibles sin intervención del usuario podría afectar objetivos, planificación, historial o privacidad de forma difícil de revertir.

## Fuerzas o criterios de decisión

- Control y comprensión por parte del usuario.
- Distinción entre recomendación y ejecución.
- Prevención de efectos secundarios involuntarios.
- Autorización backend y trazabilidad.
- Experiencia clara sin confirmaciones innecesarias.

## Decisión

Toda acción sensible originada o mediada por el agente requerirá confirmación explícita antes de aplicarse. Esto incluye activar o sustituir una rutina, modificar objetivos, aplicar progresiones o cargas, editar historial, eliminar datos, exportar o compartir datos y guardar restricciones persistentes.

Consultar datos, calcular métricas, generar una propuesta o guardar un borrador sin aplicarlo no requiere confirmación. Guardar una recomendación como propuesta tampoco aplica el cambio subyacente. La confirmación deberá asociarse a una propuesta concreta y volver a validarse en el backend.

## Alternativas consideradas

- **Confirmación explícita por acción sensible:** equilibra utilidad y control.
- **Aplicación automática con opción de deshacer:** reduce fricción, pero permite efectos no deseados antes de la revisión.
- **Agente estrictamente de lectura:** minimiza riesgo, pero impide flujos controlados de propuesta y aplicación futura.
- **Confirmación general por sesión:** es cómoda, pero demasiado amplia para cambios con distinto impacto.

## Consecuencias positivas

- El usuario conserva autoridad sobre cambios relevantes.
- Las propuestas pueden revisarse, aceptarse o rechazarse.
- Los efectos secundarios son más auditables.
- Los fallos del modelo no se convierten automáticamente en cambios persistentes.

## Consecuencias negativas

- Los flujos sensibles requieren pasos adicionales.
- Las propuestas deben tener identidad, caducidad y estado.
- La interfaz deberá explicar con precisión qué se confirmará.

## Riesgos

- Confirmaciones vagas o agrupadas que no sean informadas.
- Reutilizar una confirmación para una propuesta modificada.
- Aplicar cambios tras caducar el contexto.
- Confiar en el texto del agente en vez de validar en backend.

## Impacto en seguridad y privacidad

La confirmación complementa, pero no sustituye, autenticación, autorización, validación ni transacciones. Exportar, compartir o eliminar datos deberá mostrar alcance y destino. No se registrarán secretos ni razonamiento interno como parte de la evidencia de confirmación.

## Condiciones de revisión

Se revisará la clasificación de acciones si aparecen nuevos efectos secundarios, requisitos de privacidad o evidencia de que un flujo es demasiado permisivo o innecesariamente intrusivo. Reducir confirmaciones exigirá demostrar que la operación es de lectura o totalmente reversible y de bajo impacto.

## Documentos relacionados

- [Diseño del Agente Fitness](../architecture/agent-design.md)
- [Guardrails del agente](../safety/agent-guardrails.md)
- [Privacidad](../safety/privacy.md)
- [ADR-007 — Preservación histórica](ADR-007-historical-data-preservation.md)

