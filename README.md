# Agente Fitness

Aplicación web para registrar entrenamientos, analizar métricas y generar
rutinas y recomendaciones personalizadas mediante un agente de inteligencia
artificial.

## Estado actual

La Fase 1 de documentación fundacional está finalizada. La Fase 2 se encuentra
en progreso y ya dispone de una fundación técnica mínima: frontend React con
TypeScript, backend FastAPI, PostgreSQL local mediante Docker Compose,
SQLAlchemy, Alembic, endpoints `GET /health` y `GET /ready`, y una página
inicial que comprueba el estado de la API.

La persistencia aún no contiene modelos de negocio. La integración continua,
la contenedorización de las aplicaciones y el resto de la infraestructura de la
Fase 2 siguen pendientes.

## Inicio rápido

```powershell
Copy-Item .env.example .env
Copy-Item backend\.env.example backend\.env
docker compose up -d postgres

Set-Location backend
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

En otra terminal:

```powershell
Set-Location frontend
npm.cmd install
Copy-Item .env.example .env
npm.cmd run dev
```

Consulta la [configuración completa](docs/development/setup.md) y los
[comandos de pruebas](docs/development/testing.md). Las operaciones y
decisiones de persistencia están en la
[guía de base de datos](docs/development/database.md).

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

La aplicación disponible es únicamente una fundación técnica sin funcionalidad
fitness, autenticación, modelos de negocio ni agente de inteligencia
artificial. Docker Compose administra únicamente PostgreSQL local; todavía no
existe contenedorización completa ni despliegue de producción.
