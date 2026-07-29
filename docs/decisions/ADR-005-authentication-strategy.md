# ADR-005 — Estrategia de autenticación

- Identificador: `ADR-005`
- Estado: `Proposed`

## Contexto

El producto necesita identificar al usuario y proteger datos privados desde el backend. Todavía no se ha definido el mecanismo concreto de sesión, renovación y revocación. La elección debe servir a una experiencia web mobile-first y considerar una posible aplicación móvil futura.

## Fuerzas o criterios de decisión

- Seguridad de credenciales y tokens.
- Experiencia web y persistencia de sesión.
- Revocación, expiración y renovación.
- Protección frente a CSRF y robo de tokens.
- Complejidad de implementación y operación.
- Topología de despliegue.
- Compatibilidad futura con clientes móviles.

## Decisión propuesta

No se selecciona todavía una estrategia definitiva. Antes de implementar autenticación se realizará una evaluación de amenazas y se elegirá una alternativa documentando expiración, revocación, renovación, protección CSRF, almacenamiento en cliente y recuperación de cuenta. La identidad siempre procederá del contexto autenticado del backend, nunca de un `user_id` libre proporcionado por el cliente o el modelo.

## Alternativas consideradas

- **Sesión backend con cookie `HttpOnly`:** reduce exposición del token a JavaScript y encaja bien con web; requiere estrategia CSRF, almacenamiento de sesiones y afinidad con la topología de dominios.
- **Access token y refresh token:** facilita APIs y clientes móviles; exige rotación, revocación y almacenamiento seguro.
- **Proveedor externo de identidad:** delega capacidades maduras, pero introduce dependencia, coste, tratamiento de datos y límites de personalización.
- **Combinación de estrategias:** puede atender web y móvil, pero aumenta complejidad y riesgo de políticas inconsistentes.

## Consecuencias positivas

- Se evita fijar un mecanismo sin conocer despliegue y clientes.
- Los criterios de seguridad quedan explícitos antes de implementar.
- La autorización backend permanece como invariante independiente.

## Consecuencias negativas

- La fase de autenticación no puede comenzar sin cerrar esta decisión.
- Contratos y flujos de sesión permanecen abiertos.
- Algunas decisiones de despliegue dependen de la alternativa elegida.

## Riesgos

- Elegir por comodidad sin modelar amenazas.
- Almacenar tokens en lugares expuestos.
- Omitir revocación o rotación.
- Confundir autenticación con autorización por propietario.

## Impacto en seguridad y privacidad

La alternativa deberá minimizar datos compartidos, proteger secretos, limitar intentos y evitar incluir credenciales en logs. El backend aplicará autorización a cada recurso privado. Un proveedor externo requerirá revisar finalidad, retención y transferencias de datos sin asumir cumplimiento normativo.

## Condiciones de revisión

La propuesta deberá resolverse antes de implementar cuentas. Después se revisará ante nuevos clientes, cambios de dominio, incidentes, requisitos de inicio de sesión federado o limitaciones operativas de revocación y renovación.

## Documentos relacionados

- [Diseño conceptual de la API](../architecture/api-design.md)
- [Privacidad](../safety/privacy.md)
- [Guardrails del agente](../safety/agent-guardrails.md)
- [ADR-012 — Estrategia de despliegue](ADR-012-deployment-strategy.md)

