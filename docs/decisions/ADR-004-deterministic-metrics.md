# ADR-004 — Métricas deterministas separadas de la inteligencia artificial

- Identificador: `ADR-004`
- Estado: `Accepted`

## Contexto

Las métricas fitness influyen en observaciones, comparaciones y propuestas. Si el modelo las calculase directamente, un mismo conjunto de datos podría producir resultados distintos o difíciles de auditar. El producto necesita definiciones explícitas, manejo de datos ausentes y resultados reproducibles.

## Fuerzas o criterios de decisión

- Exactitud y repetibilidad.
- Definiciones y supuestos documentados.
- Pruebas con entradas y resultados conocidos.
- Separación entre hechos, explicaciones y sugerencias.
- Trazabilidad ante cambios de fórmula.

## Decisión

Las métricas importantes se calcularán mediante código determinista fuera del modelo. Esto incluye volumen, frecuencia, adherencia, tendencias, récords, comparaciones entre periodos, e1RM, cambios de medidas corporales y nutrición agregada. Cada métrica deberá documentar definición, unidades, supuestos y comportamiento con datos insuficientes.

El modelo podrá explicar resultados proporcionados por los servicios, relacionarlos con evidencia y formular propuestas, pero no sustituirá el motor de cálculo ni inventará valores.

## Alternativas consideradas

- **Servicios deterministas separados:** proporcionan resultados reproducibles y verificables.
- **Cálculo directo por el modelo:** reduce desarrollo inicial, pero no garantiza consistencia ni auditabilidad.
- **Enfoque híbrido sin límites estrictos:** permitiría flexibilidad, pero dificultaría saber qué resultados son hechos calculados y cuáles son inferencias.

## Consecuencias positivas

- Resultados estables para las mismas entradas.
- Pruebas unitarias con datasets conocidos.
- Fórmulas revisables y versionables.
- Explicaciones del agente basadas en evidencia.

## Consecuencias negativas

- Cada métrica requiere definición e implementación explícitas.
- Los cambios de fórmula exigen revisar comparabilidad histórica.
- El agente no podrá improvisar métricas nuevas como si fueran oficiales.

## Riesgos

- Presentar una estimación como medición exacta.
- Cambiar fórmulas sin registrar sus efectos.
- Calcular con datos incompletos sin indicarlo.
- Duplicar lógica entre servicios o clientes.

## Impacto en seguridad y privacidad

Los servicios solo deben consultar datos autorizados del usuario autenticado y devolver el mínimo necesario. Las explicaciones no deben revelar registros ajenos ni datos sensibles innecesarios. Las métricas de salud o nutrición no deben presentarse como diagnóstico ni validación clínica.

## Condiciones de revisión

La separación deberá revisarse si una métrica deja de ser reproducible, cambia su definición de dominio o aparece una técnica probabilística necesaria. Cualquier excepción tendrá que documentar incertidumbre, validación y límites sin convertir la salida del modelo en fuente de verdad.

## Documentos relacionados

- [Principios](../PRINCIPIOS.md)
- [Glosario](../GLOSARIO.md)
- [Arquitectura general](../architecture/overview.md)
- [Diseño del Agente Fitness](../architecture/agent-design.md)

