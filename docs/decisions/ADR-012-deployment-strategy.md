# ADR-012 — Estrategia de despliegue

- Identificador: `ADR-012`
- Estado: `Proposed`

## Contexto

La arquitectura prevé frontend, backend y PostgreSQL, pero no existe infraestructura operativa ni una topología de producción elegida. Docker Compose está previsto para desarrollo local y no constituye una estrategia definitiva de producción.

## Fuerzas o criterios de decisión

- Coste total y simplicidad operativa.
- Gestión de secretos y aislamiento.
- Backups, restauración y disponibilidad de PostgreSQL.
- Escalabilidad y rendimiento.
- Observabilidad y respuesta a incidentes.
- Despliegues reproducibles y reversibles.
- Relación entre dominios de frontend, API y autenticación.

## Decisión propuesta

No se selecciona todavía una plataforma ni topología de producción. Antes del despliegue se compararán alternativas con estimaciones de coste, modelo de amenazas, gestión de secretos, backups probados, observabilidad, recuperación y procedimiento reproducible de publicación. Docker Compose se limitará al entorno local previsto salvo una decisión posterior explícita.

## Alternativas consideradas

- **Plataforma gestionada:** reduce operación inicial, pero introduce dependencia, límites de configuración y coste variable.
- **Contenedores en infraestructura propia:** ofrece control, con mayor responsabilidad de seguridad, parches y disponibilidad.
- **Frontend y backend separados:** permite escalar y publicar de forma independiente, pero complica dominios, CORS, cookies y observabilidad.
- **Despliegue conjunto:** simplifica topología inicial, aunque acopla ciclos y escalado.
- **PostgreSQL administrado:** delega operación y backups, con coste y dependencia del proveedor.
- **PostgreSQL autogestionado:** aumenta control, pero también riesgo y carga operativa.

## Consecuencias positivas

- Se evita confundir el entorno local con producción.
- La selección incluirá seguridad, backups y recuperación.
- Las dependencias con autenticación quedarán visibles.

## Consecuencias negativas

- No existe aún una ruta de producción cerrada.
- Presupuestos y procedimientos operativos permanecen pendientes.
- Algunas decisiones de autenticación y observabilidad dependen de la topología.

## Riesgos

- Elegir una plataforma sin probar restauración.
- Exponer secretos o bases de datos.
- Crear despliegues manuales no reproducibles.
- Subestimar costes, bloqueo de proveedor o necesidades de observabilidad.

## Impacto en seguridad y privacidad

La solución deberá aplicar mínimo privilegio, cifrado en tránsito, gestión externa de secretos, aislamiento de PostgreSQL, logs minimizados y backups protegidos. Todo proveedor deberá revisarse por su tratamiento de datos sin asumir cumplimiento legal.

## Condiciones de revisión

La propuesta deberá resolverse antes de un entorno de producción. Se revisará ante cambios de escala, presupuesto, regiones, proveedores, requisitos de recuperación, incidentes o una estrategia de autenticación incompatible con la topología.

## Documentos relacionados

- [Arquitectura general](../architecture/overview.md)
- [Roadmap](../ROADMAP.md)
- [Privacidad](../safety/privacy.md)
- [ADR-005 — Estrategia de autenticación](ADR-005-authentication-strategy.md)

