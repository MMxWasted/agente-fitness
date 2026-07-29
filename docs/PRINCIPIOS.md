# Principios de Agente Fitness

Este documento define los principios permanentes del proyecto. Su propósito es orientar decisiones de producto, arquitectura y desarrollo sin convertir el proyecto en una solución excesivamente compleja desde el inicio.

## 1. Propiedad del usuario sobre sus datos

- Descripción: El usuario conserva la titularidad y el control de sus datos personales y de actividad.
- Consecuencia práctica: El sistema debe permitir el acceso, la exportación y la eliminación de datos de forma comprensible, y no debe exponer información ajena ni reutilizarla sin una base explícita.

## 2. El agente es asistente, no fuente de verdad

- Descripción: La inteligencia artificial puede interpretar datos y proponer acciones, pero no sustituye la validación humana ni la autoridad del sistema determinista.
- Consecuencia práctica: Las respuestas del agente deben mostrar evidencias, límites y contexto, y no deben imponerse como hechos absolutos.

## 3. Los cálculos importantes son deterministas y reproducibles

- Descripción: Las métricas de negocio relevantes deben calcularse mediante lógica explícita y verificable, no mediante inferencias del modelo.
- Consecuencia práctica: El backend debe separar los servicios de analítica determinista de las capacidades del agente y documentar las reglas de cálculo.

## 4. Las recomendaciones deben mostrar evidencias

- Descripción: Toda recomendación debe basarse en datos y debe indicar qué información la sustenta.
- Consecuencia práctica: El sistema debe registrar o exponer la evidencia utilizada y distinguir entre observación, recomendación y propuesta.

## 5. Las acciones relevantes requieren confirmación

- Descripción: Cambios importantes sobre rutinas, objetivos, datos históricos o registros sensibles deben requerir una confirmación explícita del usuario.
- Consecuencia práctica: El flujo de interacción debe incluir una etapa de revisión antes de aplicar cualquier cambio significativo.

## 6. El producto será mobile-first

- Descripción: La experiencia principal debe funcionar bien en pantallas pequeñas y en contextos de uso realista, como registrar entrenamientos o consultar datos en movimiento.
- Consecuencia práctica: La interfaz debe priorizar simplicidad, navegación clara y reducción de fricción en dispositivos móviles.

## 7. Simplicidad frente a sobreingeniería

- Descripción: El proyecto debe avanzar de forma incremental y evitar construir componentes complejos antes de que exista una necesidad demostrada.
- Consecuencia práctica: Cada decisión técnica debe justificarse por un problema concreto y se preferirá una solución simple y observable.

## 8. Seguridad y privacidad desde el diseño

- Descripción: La seguridad, la privacidad y la integridad de los datos forman parte del diseño del producto y no se añadirán como capas posteriores.
- Consecuencia práctica: La autenticación, la autorización, el manejo de secretos y el tratamiento de datos sensibles deben considerarse desde las primeras fases.

## 9. Integridad de los datos históricos

- Descripción: Los registros históricos deben conservarse de forma estable y no deben alterarse de forma implícita cuando cambien las rutinas o las reglas de negocio.
- Consecuencia práctica: Las operaciones de edición deben tener reglas claras y los datos históricos deben tratarse como inmutables salvo que exista un mecanismo explícito.

## 10. Implementación incremental

- Descripción: El producto se desarrollará por etapas verificables, con entregables claros y sin asumir que todas las capacidades deben estar presentes desde el inicio.
- Consecuencia práctica: Cada fase debe tener criterios de aceptación, dependencias y límite de alcance claramente definidos.

## 11. El agente no realizará diagnósticos médicos

- Descripción: El agente puede apoyar en hábitos, seguimiento y recomendaciones generales, pero no debe sustituir el criterio clínico ni ofrecer diagnósticos médicos.
- Consecuencia práctica: El sistema debe incluir guardrails, límites explícitos y respuestas seguras cuando el contexto sugiera riesgo de salud.

## 12. Las decisiones arquitectónicas importantes se documentan mediante ADR

- Descripción: Las decisiones con impacto en la arquitectura, el producto o la seguridad deben registrarse formalmente.
- Consecuencia práctica: Cuando una decisión afecte a la estructura del sistema, su justificación y sus consecuencias deben dejarse documentadas antes de ampliarla.
