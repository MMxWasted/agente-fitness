# ADR-002 — PostgreSQL como base de datos relacional

- Identificador: `ADR-002`
- Estado: `Accepted`

## Contexto

El dominio contiene usuarios, rutinas, ejercicios, sesiones, series, medidas, nutrición y registros del agente con relaciones, propiedad e invariantes. También requiere transacciones, historial estable y agregaciones temporales. La base de datos todavía no está implementada.

## Fuerzas o criterios de decisión

- Integridad referencial y restricciones.
- Transacciones para operaciones de varios pasos.
- Consultas históricas y agregaciones.
- Índices y evolución mediante migraciones.
- Capacidad de representar datos semiestructurados de forma limitada.
- Madurez operativa y disponibilidad de herramientas.

## Decisión

PostgreSQL será la base de datos relacional prevista para la persistencia principal. Se utilizarán relaciones, restricciones, transacciones e índices para proteger el dominio. `JSONB` podrá emplearse cuando una estructura semiestructurada esté justificada, sin sustituir indiscriminadamente el modelado relacional. La elección de SQLAlchemy y Alembic continúa pendiente de implementación y validación; este ADR no afirma que estén configurados.

## Alternativas consideradas

- **PostgreSQL:** ofrece integridad, transacciones, agregaciones, índices y `JSONB`.
- **MongoDB:** aporta flexibilidad documental, pero desplaza parte de la integridad relacional y complica invariantes transversales.
- **SQLite:** es simple para prototipos, pero no es la dirección principal para concurrencia y operación del producto.
- **Combinación de bases de datos:** podría optimizar casos específicos, pero añade consistencia distribuida y carga operativa sin una necesidad actual.

## Consecuencias positivas

- Las relaciones de propiedad pueden reforzarse en persistencia.
- Las operaciones sensibles pueden agruparse en transacciones.
- El historial y las agregaciones cuentan con capacidades maduras.
- Existe una ruta clara para migraciones e índices.

## Consecuencias negativas

- Requiere operación, copias de seguridad y mantenimiento.
- Los cambios de esquema deberán gestionarse con disciplina.
- `JSONB` mal utilizado puede ocultar esquemas inestables.

## Riesgos

- Diseñar el esquema antes de cerrar invariantes del dominio.
- Confiar solo en restricciones de base de datos para autorización.
- Crear consultas costosas sin índices ni límites temporales.

## Impacto en seguridad y privacidad

El acceso deberá limitarse al backend y seguir mínimo privilegio. La autorización por usuario no se delega a la base de datos ni al agente. Cifrado, backups, restauración, retención y eliminación deberán documentarse antes de producción.

## Condiciones de revisión

Se revisará si aparecen requisitos demostrables que PostgreSQL no pueda satisfacer razonablemente, restricciones operativas incompatibles o un caso de uso especializado que justifique otra tecnología sin debilitar integridad y privacidad.

## Documentos relacionados

- [Modelo de datos conceptual](../architecture/data-model.md)
- [Arquitectura general](../architecture/overview.md)
- [Privacidad](../safety/privacy.md)

