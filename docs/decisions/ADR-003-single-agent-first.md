# ADR-003 — Un único agente inicialmente

- Identificador: `ADR-003`
- Estado: `Accepted`

## Contexto

El Agente Fitness debe explicar datos, generar propuestas y coordinar herramientas autorizadas sin acceder directamente a SQL ni modificar información sensible por iniciativa propia. Una arquitectura con varios agentes aumentaría la superficie de coordinación y evaluación antes de demostrar valor.

## Fuerzas o criterios de decisión

- Simplicidad de orquestación y observabilidad.
- Autorización consistente en todas las herramientas.
- Facilidad para probar selección de herramientas y guardrails.
- Coste, latencia y límites de contexto.
- Necesidad de especialización demostrable.

## Decisión

La primera versión utilizará un único agente orquestador con una lista cerrada de herramientas. Los cálculos y reglas de negocio permanecerán en servicios deterministas. Solo se crearán nuevas especializaciones o agentes si existe una necesidad medible que no pueda resolverse razonablemente mediante herramientas, servicios o separación interna de responsabilidades.

## Alternativas consideradas

- **Único agente:** reduce coordinación, trazabilidad y puntos de fallo.
- **Arquitectura multiagente:** permitiría especialización, pero introduce delegación, estados intermedios, más coste y nuevas evaluaciones de seguridad.
- **Ausencia de agente y flujos completamente deterministas:** maximiza previsibilidad, pero no cubre la explicación conversacional y la generación controlada de propuestas previstas.

## Consecuencias positivas

- Menor complejidad inicial.
- Una política central de herramientas, contexto y salida.
- Evaluaciones más acotadas.
- Trazabilidad más comprensible para fallos y decisiones.

## Consecuencias negativas

- El orquestador podría acumular demasiadas responsabilidades.
- Un único contexto puede resultar insuficiente para tareas futuras complejas.
- La especialización queda limitada hasta que se justifique.

## Riesgos

- Convertir el agente en una capa monolítica.
- Añadir herramientas sin límites claros.
- Confundir la comodidad conversacional con autoridad de negocio.

## Impacto en seguridad y privacidad

El agente operará con contexto autenticado inyectado por el servidor y datos mínimos. Cada herramienta aplicará autorización propia. La concentración de capacidades exige esquemas cerrados, trazabilidad y pruebas de prompt injection, acceso cruzado y fallos de herramientas.

## Condiciones de revisión

Se revisará si las evaluaciones muestran degradación medible por exceso de responsabilidades, si existen dominios con contextos o permisos incompatibles, o si un diseño especializado mejora calidad, coste o seguridad con evidencia reproducible.

## Documentos relacionados

- [Diseño del Agente Fitness](../architecture/agent-design.md)
- [Guardrails del agente](../safety/agent-guardrails.md)
- [Plan maestro](../PLAN_MAESTRO.md)

