# ADR-009 — Almacenamiento de conversaciones

- Identificador: `ADR-009`
- Estado: `Proposed`

## Contexto

Las conversaciones pueden aportar continuidad, evidencia visible y soporte, pero también contienen datos personales y contexto sensible. Los distintos elementos de una interacción no tienen la misma finalidad: mensajes visibles, instrucciones internas, herramientas y trazas técnicas requieren tratamientos separados.

## Fuerzas o criterios de decisión

- Utilidad y continuidad para el usuario.
- Consentimiento y expectativas comprensibles.
- Minimización y limitación de finalidad.
- Retención, exportación y eliminación.
- Depuración y evaluación sin recopilar datos excesivos.
- Coste y complejidad operativa.

## Decisión propuesta

No se selecciona todavía una política final de almacenamiento y retención. Se evaluará por separado si se conservan mensajes visibles, resúmenes, trazas técnicas y ejecuciones de herramientas. El razonamiento interno del modelo no se almacenará.

Los prompts del sistema y las instrucciones internas no se tratarán como mensajes de conversación. Los argumentos y resultados completos de herramientas no se registrarán por defecto; las trazas técnicas deberán limitarse a identificadores, estados, tiempos, resúmenes y códigos de error cuando sea suficiente. La decisión final deberá definir consentimiento, finalidad, acceso, exportación, eliminación y plazos.

## Alternativas consideradas

- **No almacenar conversaciones:** minimiza datos, pero elimina continuidad e historial visible.
- **Almacenar mensajes visibles:** conserva la experiencia, con mayor responsabilidad de retención y acceso.
- **Almacenar resúmenes:** reduce volumen, aunque puede perder detalle o introducir interpretación.
- **Almacenamiento temporal:** permite continuidad limitada, pero requiere caducidad fiable.
- **Modelo híbrido:** combina mensajes, resúmenes o temporalidad según finalidad, a costa de más reglas.

## Consecuencias positivas

- Se evita mezclar categorías de datos con finalidades distintas.
- La política podrá diseñarse alrededor de consentimiento y minimización.
- Queda prohibido conservar razonamiento interno.

## Consecuencias negativas

- La persistencia de conversaciones no puede implementarse aún de forma definitiva.
- Un modelo híbrido puede ser difícil de explicar y operar.
- Los resúmenes requieren reglas de calidad y corrección.

## Riesgos

- Retener datos sensibles sin finalidad suficiente.
- Registrar payloads completos por comodidad técnica.
- Crear resúmenes inexactos usados como hechos.
- No propagar eliminación a copias, índices o backups.

## Impacto en seguridad y privacidad

El acceso estará limitado al usuario autenticado y a componentes autorizados. Se aplicarán minimización, cifrado y exclusión de secretos. No se afirmará cumplimiento legal hasta contar con revisión especializada y una política operativa completa.

## Condiciones de revisión

La propuesta deberá resolverse antes de habilitar persistencia de conversaciones. Se revisará ante cambios de proveedor, nuevas finalidades, incidentes, evaluaciones de utilidad o requisitos de consentimiento, retención, exportación y eliminación.

## Documentos relacionados

- [Privacidad](../safety/privacy.md)
- [Modelo de datos conceptual](../architecture/data-model.md)
- [Diseño del Agente Fitness](../architecture/agent-design.md)
- [ADR-010 — Exportación y eliminación](ADR-010-data-export-deletion.md)

