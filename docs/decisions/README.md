# Decisiones arquitectónicas

## Propósito

Un Architecture Decision Record (ADR) documenta una decisión arquitectónica relevante, el contexto en el que se toma, las alternativas evaluadas y sus consecuencias. Los ADR describen la dirección del proyecto; no demuestran que exista una implementación.

## Estados

- `Accepted`: la dirección arquitectónica ha sido adoptada, aunque todavía no exista código.
- `Proposed`: el problema y las alternativas están documentados, pero la decisión definitiva sigue pendiente.
- `Superseded`: una decisión posterior sustituye expresamente este ADR.
- `Deprecated`: la decisión ya no debe aplicarse y no ha sido reemplazada por otra equivalente.

## Índice

| Identificador | Título | Estado | Documento |
| --- | --- | --- | --- |
| ADR-001 | Monorepo | Accepted | [ADR-001](ADR-001-monorepo.md) |
| ADR-002 | PostgreSQL como base de datos relacional | Accepted | [ADR-002](ADR-002-postgresql.md) |
| ADR-003 | Un único agente inicialmente | Accepted | [ADR-003](ADR-003-single-agent-first.md) |
| ADR-004 | Métricas deterministas separadas de la inteligencia artificial | Accepted | [ADR-004](ADR-004-deterministic-metrics.md) |
| ADR-005 | Estrategia de autenticación | Accepted | [ADR-005](ADR-005-authentication-strategy.md) |
| ADR-006 | Versionado de rutinas | Proposed | [ADR-006](ADR-006-routine-versioning.md) |
| ADR-007 | Preservación de datos históricos | Accepted | [ADR-007](ADR-007-historical-data-preservation.md) |
| ADR-008 | Confirmaciones para acciones sensibles del agente | Accepted | [ADR-008](ADR-008-agent-confirmations.md) |
| ADR-009 | Almacenamiento de conversaciones | Proposed | [ADR-009](ADR-009-conversation-storage.md) |
| ADR-010 | Exportación y eliminación de datos | Accepted | [ADR-010](ADR-010-data-export-deletion.md) |
| ADR-011 | Biblioteca de componentes de interfaz | Proposed | [ADR-011](ADR-011-component-library.md) |
| ADR-012 | Estrategia de despliegue | Proposed | [ADR-012](ADR-012-deployment-strategy.md) |
| ADR-013 | Gestión de sesión web renovable | Accepted | [ADR-013](ADR-013-session-management.md) |
| ADR-014 | Importación manual y versionada de mediciones desde XLSX | Accepted | [ADR-014](ADR-014-body-measurement-xlsx-import.md) |

## Reglas para nuevos ADR

1. Asignar el siguiente identificador correlativo y un nombre de archivo descriptivo.
2. Explicar contexto, criterios, decisión o propuesta, alternativas, consecuencias, riesgos, impacto en seguridad y privacidad, condiciones de revisión y documentos relacionados.
3. Usar `Proposed` cuando no se haya elegido una alternativa y `Accepted` solo cuando exista una dirección explícita.
4. No presentar una dirección documental como implementación existente.
5. Enlazar el ADR desde este índice y revisar la coherencia con la arquitectura, el producto y la seguridad.

## Sustitución de decisiones

Una decisión `Accepted` no debe modificarse silenciosamente para expresar una dirección incompatible. El cambio debe documentarse en un nuevo ADR, que referencie al anterior y explique el motivo. El ADR sustituido pasa a `Superseded` e indica el identificador de la decisión que lo reemplaza.
