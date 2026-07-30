# Changelog

## [Unreleased]

### Added

- Estructura inicial del monorepo con áreas independientes para frontend y backend.
- Frontend React con TypeScript generado desde la plantilla oficial de Vite.
- Backend FastAPI administrado mediante uv.
- Endpoint de salud `GET /health` con respuesta tipada.
- Página inicial mínima con estados de comprobación, disponibilidad y error de la API.
- Herramientas iniciales de linting, tipos y pruebas para frontend y backend.
- Documentación reproducible de configuración y verificaciones del entorno.
- PostgreSQL local mediante Docker Compose, con volumen persistente y
  comprobación de salud.
- Configuración tipada de `DATABASE_URL` e infraestructura síncrona mínima de
  SQLAlchemy con Psycopg.
- Línea base técnica de Alembic sin tablas de negocio.
- Endpoint de readiness `GET /ready` con contratos 200 y 503 controlados.
- Pruebas unitarias de configuración, ciclo de sesión y disponibilidad de la
  base sin depender de PostgreSQL externo.
- Documentación reproducible de operaciones y migraciones de la base local.
- Workflow mínimo de GitHub Actions con jobs independientes para frontend,
  calidad backend e integración PostgreSQL.
- Validación automatizada de Compose, ciclo reversible de Alembic y contratos
  HTTP de liveness y readiness contra un PostgreSQL efímero.
- Scripts PowerShell reproducibles para preparar, iniciar, comprobar y detener
  PostgreSQL, FastAPI y Vite en desarrollo local.
- Gestión local segura de procesos mediante PID y hora de inicio, con logs y
  estado temporal excluidos de Git.
- Comprobación conjunta de Docker, PostgreSQL, Alembic, `/health`, `/ready` y
  frontend, con eliminación del volumen solo mediante una opción explícita.
- Validación local de extremo a extremo del arranque reproducible, incluidos el
  reinicio, Alembic en `head` y la persistencia del volumen PostgreSQL.
- Modelo PostgreSQL mínimo de usuario con UUID, correo normalizado único,
  estado activo y timestamps UTC, creado mediante una migración reversible.
- Registro de cuenta, emisión de access tokens bearer y consulta autenticada
  del usuario actual mediante `/api/v1`.
- Protección de contraseñas con Argon2id y validación JWT de firma, caducidad y
  claims obligatorios.
- Pruebas unitarias de identidad y seguridad, junto con pruebas de integración
  repetibles sobre una base PostgreSQL específica de test.
- Configuración JWT tipada, generación segura del secreto local y ejecución de
  la integración de autenticación en el job `PostgreSQL integration`.
- Gestión de sesión web renovable con refresh token opaco en cookie `HttpOnly`,
  digest exclusivo en PostgreSQL, rotación atómica y logout revocable.
- Interfaz React mínima de login, restauración y cierre de sesión, con access
  token conservado únicamente en memoria.
- Protección CSRF mediante orígenes explícitos, CORS con credenciales y
  configuración de cookie validada por entorno.
- Migración reversible de `auth_sessions` y cobertura unitaria, frontend y de
  integración PostgreSQL, incluida la renovación concurrente.
- Visión de producto ampliada para el MVP inicial de Agente Fitness.
- Alcance del producto reestructurado con clasificación MoSCoW y criterios de éxito.
- Historias de usuario completas y verificables para las épicas principales del producto.
- Guía de contribución con referencias a la documentación de desarrollo.
- Workflow de Git y colaboración con reglas de ramas, commits, pull requests y revisión.
- Definition of Done con criterios separados por documentación, backend, frontend, base de datos, analítica determinista y Agente Fitness.
- Arquitectura general prevista para el sistema, incluyendo contexto, componentes y flujos.
- Modelo de datos conceptual con entidades, relaciones, propiedad, historial y decisiones pendientes.
- Diseño conceptual de la API con recursos, autenticación, autorización, errores y versionado.
- Diseño del Agente Fitness con herramientas conceptuales, flujos, salidas estructuradas y controles.
- Documentación de seguridad de fitness, nutrición y salud.
- Documentación de privacidad y tratamiento de datos.
- Guardrails conceptuales del Agente Fitness.
- Índice de decisiones arquitectónicas del proyecto.
- ADR iniciales aceptados para las direcciones arquitectónicas ya adoptadas.
- ADR iniciales propuestos para las decisiones que requieren evaluación adicional.
