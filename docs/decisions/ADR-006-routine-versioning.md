# ADR-006 — Versionado de rutinas

- Identificador: `ADR-006`
- Estado: `Proposed`

## Contexto

Las rutinas cambian con el tiempo, pero una sesión finalizada debe conservar qué se planificó y qué se ejecutó. El modelo conceptual exige estabilidad histórica, aunque no determina todavía si se lograrán mediante versiones completas, snapshots, copias de campos o una combinación.

## Fuerzas o criterios de decisión

- Fidelidad del contexto histórico.
- Simplicidad de consulta y corrección.
- Coste de almacenamiento.
- Evolución del esquema.
- Trazabilidad de sustituciones y progresiones.
- Integridad transaccional.

## Decisión propuesta

No se elige todavía el mecanismo definitivo. Toda alternativa deberá preservar la rutina original relevante, el ejercicio planificado, el ejercicio realizado, cargas y series previstas necesarias, sustituciones, valores reales y contexto de sesiones terminadas. La solución deberá diferenciar la edición de planificación futura de una corrección histórica explícita.

## Alternativas consideradas

- **Versiones completas inmutables:** conservan una fotografía coherente de cada rutina, con mayor almacenamiento y gestión de versiones.
- **Snapshots parciales en sesiones:** guardan el contexto necesario al ejecutar, pero requieren definir con precisión qué se copia.
- **Copia de valores relevantes:** simplifica lectura histórica, aunque puede duplicar datos y perder relaciones si el conjunto es insuficiente.
- **Modelo híbrido:** combina versiones de rutina y datos materializados en sesiones; ofrece resiliencia a costa de más reglas de consistencia.

## Consecuencias positivas

- Los requisitos mínimos de preservación quedan fijados antes del esquema.
- Las alternativas pueden evaluarse con casos históricos concretos.
- Se evita acoplar sesiones finalizadas a la rutina editable actual.

## Consecuencias negativas

- El esquema y las migraciones de rutinas no pueden cerrarse todavía.
- Habrá que definir reconciliación entre versiones, copias y catálogo.
- La estrategia elegida puede aumentar almacenamiento o complejidad.

## Riesgos

- Copiar pocos campos y perder contexto.
- Duplicar datos sin una fuente de verdad definida.
- Permitir actualizaciones en cascada sobre sesiones terminadas.
- Confundir una corrección explícita con edición ordinaria.

## Impacto en seguridad y privacidad

Las copias históricas también son datos privados y deben cumplir autorización, exportación y eliminación. La duplicación puede ampliar la superficie de retención. Las trazas de corrección deben evitar información sensible innecesaria y preservar al usuario autenticado como propietario.

## Condiciones de revisión

La propuesta deberá resolverse antes de diseñar las tablas definitivas de rutinas y sesiones. Se revisará si los casos de sustitución, archivado, corrección, exportación o eliminación no pueden representarse sin pérdida o ambigüedad.

## Documentos relacionados

- [Modelo de datos conceptual](../architecture/data-model.md)
- [ADR-007 — Preservación de datos históricos](ADR-007-historical-data-preservation.md)
- [Plan maestro](../PLAN_MAESTRO.md)

