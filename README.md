# Agente Fitness

Aplicación web para registrar entrenamientos, analizar métricas y generar
rutinas y recomendaciones personalizadas mediante un agente de inteligencia
artificial.

## Estado actual

Las fases 1 y 2 están finalizadas. La Fase 3 está en progreso y ya incorpora
identidad, autenticación backend y gestión de sesión web: registro por correo,
contraseña protegida con Argon2id, access tokens JWT, refresh opaco rotatorio,
logout con revocación y consulta de la cuenta actual. El frontend React ofrece
un formulario mínimo de login, restaura la sesión y conserva el access token
solo en memoria.

La integración continua mantiene tres jobs independientes y ejecuta pruebas
reales de autenticación y sesiones contra un PostgreSQL efímero. Los scripts
PowerShell preparan, inician, comprueban y detienen el entorno local sin
Dockerizar frontend ni backend; su recorrido completo con Docker ya fue
validado.

## Inicio rápido

```powershell
.\scripts\setup-dev.ps1
.\scripts\start-dev.ps1
.\scripts\check-dev.ps1
```

Al terminar, ejecuta `.\scripts\stop-dev.ps1`. La parada habitual conserva el
volumen PostgreSQL.

Consulta la [configuración completa](docs/development/setup.md) y los
[comandos de pruebas](docs/development/testing.md). Las operaciones y
decisiones de persistencia están en la
[guía de base de datos](docs/development/database.md).

## Integración continua

El workflow `CI` se ejecuta en pull requests dirigidas a `main`, pushes sobre
`main` y ejecuciones manuales. Sus jobs independientes comprueban el frontend,
la calidad del backend y la integración real con un PostgreSQL efímero.

Consulta la [guía de pruebas](docs/development/testing.md#integración-continua)
para ver los comandos equivalentes, el diagnóstico de fallos y las
comprobaciones validadas que deberían proteger `main`.

## Objetivo general

Construir una base sólida para un producto de seguimiento fitness, analítica determinista y asistencia guiada por inteligencia artificial, manteniendo un enfoque centrado en el usuario, la privacidad y la integridad de los datos históricos.

## Documentación principal

### Planificación y visión

- [Plan maestro](docs/PLAN_MAESTRO.md)
- [Principios](docs/PRINCIPIOS.md)
- [Roadmap](docs/ROADMAP.md)
- [Glosario](docs/GLOSARIO.md)
- [Convenciones](docs/CONVENCIONES.md)
- [Workflow de Codex](docs/CODEX_WORKFLOW.md)

### Producto

- [Visión de producto](docs/product/vision.md)
- [Alcance del producto](docs/product/scope.md)
- [Historias de usuario](docs/product/user-stories.md)

### Arquitectura y seguridad

- [Arquitectura general](docs/architecture/overview.md)
- [Modelo de datos conceptual](docs/architecture/data-model.md)
- [Diseño conceptual de la API](docs/architecture/api-design.md)
- [Diseño del Agente Fitness](docs/architecture/agent-design.md)
- [Seguridad fitness](docs/safety/fitness-safety.md)
- [Privacidad](docs/safety/privacy.md)
- [Guardrails del agente](docs/safety/agent-guardrails.md)

### Decisiones arquitectónicas

- [Índice de ADR](docs/decisions/README.md)

### Colaboración y desarrollo

- [Contributing](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)
- [Configuración del entorno](docs/development/setup.md)
- [Base de datos local](docs/development/database.md)
- [Pruebas y verificaciones](docs/development/testing.md)
- [Workflow de Git y colaboración](docs/development/git-workflow.md)
- [Definición de done](docs/development/definition-of-done.md)

## Aviso importante

La aplicación disponible incorpora la cuenta técnica, autenticación backend y
una interfaz mínima de login y sesión. No existe todavía interfaz de registro,
perfil fitness, rutinas, entrenamientos, métricas ni Agente Fitness. Docker
Compose administra únicamente PostgreSQL local; no existe contenedorización
completa ni despliegue de producción. Los scripts locales ejecutan FastAPI y
Vite como procesos del host registrados de forma explícita.
