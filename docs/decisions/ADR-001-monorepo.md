# ADR-001 — Monorepo

- Identificador: `ADR-001`
- Estado: `Accepted`

## Contexto

Agente Fitness necesita coordinar una futura aplicación React con TypeScript, una API FastAPI, documentación, infraestructura local y automatizaciones. Estas áreas evolucionarán a ritmos distintos, pero compartirán contratos, reglas de dominio y decisiones de seguridad. La estructura sigue siendo una dirección arquitectónica: no implica que todos los componentes estén creados.

## Fuerzas o criterios de decisión

- Mantener cambios coordinados entre frontend, backend y documentación.
- Conservar una fuente de verdad común para contratos y reglas.
- Facilitar revisiones transversales y trazabilidad.
- Evitar acoplamiento accidental entre áreas.
- Controlar el alcance de CI y el crecimiento del repositorio.

## Decisión

Se mantendrán frontend, backend, documentación, infraestructura y automatización en un único repositorio. Cada área tendrá límites y responsabilidades explícitos. Los comandos, dependencias y pipelines deberán poder dirigirse al área afectada cuando resulte práctico.

## Alternativas consideradas

- **Monorepo:** concentra historia, contratos y documentación; exige límites claros y CI selectiva.
- **Repositorios separados:** mejora el aislamiento operativo, pero complica cambios coordinados y puede fragmentar la documentación.
- **Repositorio principal con componentes externos:** permite separar piezas especializadas, pero añade gestión de versiones y sincronización antes de que exista una necesidad concreta.

## Consecuencias positivas

- Los cambios de contrato pueden revisarse junto con sus consumidores.
- La documentación y las decisiones permanecen centralizadas.
- Resulta más sencillo mantener una visión coherente del producto.
- Las automatizaciones comunes pueden compartir convenciones.

## Consecuencias negativas

- La CI puede abarcar más áreas y requerir filtrado por rutas.
- El repositorio crecerá con el producto.
- Una organización deficiente podría mezclar responsabilidades o dependencias.

## Riesgos

- Introducir dependencias transversales innecesarias.
- Ejecutar validaciones costosas para cambios aislados.
- Convertir la raíz del repositorio en un espacio sin propiedad clara.

## Impacto en seguridad y privacidad

La centralización facilita revisar contratos y controles de seguridad de extremo a extremo, pero aumenta la importancia de aplicar mínimo privilegio a secretos, automatizaciones y permisos. Ningún secreto debe almacenarse en el repositorio, y el frontend no debe acceder a credenciales del backend.

## Condiciones de revisión

La decisión deberá revisarse si aparecen equipos con ciclos de publicación realmente independientes, requisitos de acceso incompatibles, límites de escala de CI no mitigables o componentes que necesiten distribución y versionado autónomos.

## Documentos relacionados

- [Plan maestro](../PLAN_MAESTRO.md)
- [Arquitectura general](../architecture/overview.md)
- [Roadmap](../ROADMAP.md)

