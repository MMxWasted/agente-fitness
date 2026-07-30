# Base de datos local y persistencia técnica

## Alcance

El bloque 2B.1 incorpora PostgreSQL local, conexión con SQLAlchemy 2 y
migraciones Alembic. Esta base permite verificar la infraestructura sin
introducir entidades, repositorios ni lógica de negocio.

## Decisiones de implementación

- PostgreSQL se ejecuta como único servicio de `compose.yaml`.
- La imagen se fija explícitamente en `postgres:18.4`.
- Los datos viven en el volumen nombrado
  `agente_fitness_postgres_data`.
- SQLAlchemy usa el driver Psycopg 3 y una URL
  `postgresql+psycopg://`.
- El acceso es síncrono. Es la opción mínima para el endpoint técnico y las
  migraciones actuales; no existe todavía una carga de negocio que justifique
  la complejidad adicional de una pila asíncrona.
- El engine y la fábrica de sesiones se crean de forma perezosa. Importar la
  aplicación no abre conexiones.
- El timeout inicial de conexión es configurable y vale 3 segundos por
  defecto, para que readiness falle de forma controlada cuando PostgreSQL no
  está disponible.
- La dependencia FastAPI entrega una sesión por solicitud y siempre la cierra.
- Alembic comparte `DATABASE_URL` y `Base.metadata` con la aplicación.

La revisión inicial es deliberadamente vacía. Solo establece la línea base de
migraciones y no simula tablas futuras.

## Contratos de diagnóstico

| Ruta | Objetivo | Consulta PostgreSQL | Respuesta |
| --- | --- | --- | --- |
| `GET /health` | Liveness del proceso | Ninguna | 200 `{"status":"ok"}` |
| `GET /ready` | Disponibilidad para usar persistencia | `SELECT 1` | 200 `{"status":"ready"}` o 503 `{"status":"unavailable"}` |

La respuesta de readiness no incluye URL, usuario, contraseña, traza ni
detalles internos del error.

## Operaciones habituales

Los comandos parten de la raíz y funcionan en PowerShell después de copiar los
archivos `.env.example`, como explica la
[guía de configuración](setup.md).

Validar e iniciar PostgreSQL:

```powershell
docker compose config
docker compose up -d postgres
docker compose ps
```

Aplicar y consultar migraciones:

```powershell
Set-Location backend
uv run alembic upgrade head
uv run alembic current
Set-Location ..
```

Comprobar que la revisión es reversible:

```powershell
Set-Location backend
uv run alembic downgrade base
uv run alembic upgrade head
Set-Location ..
```

Detener PostgreSQL conservando los datos:

```powershell
docker compose down
```

Eliminar también el volumen local, únicamente cuando se quiera perder todos
los datos:

```powershell
docker compose down --volumes
```

## Verificación manual

Con PostgreSQL healthy, la migración aplicada y Uvicorn iniciado:

```powershell
$health = Invoke-WebRequest http://127.0.0.1:8000/health
$health.StatusCode
$health.Content

$ready = Invoke-WebRequest http://127.0.0.1:8000/ready
$ready.StatusCode
$ready.Content
```

Los resultados esperados son 200 con `{"status":"ok"}` y 200 con
`{"status":"ready"}`. Al detener PostgreSQL, `/health` debe seguir devolviendo
200 y `/ready` debe devolver 503 con `{"status":"unavailable"}`.

La validación Docker/PostgreSQL no pudo ejecutarse en el entorno donde se creó
el bloque porque el binario `docker` no estaba disponible. No debe darse por
superada hasta completar este procedimiento en un equipo con Docker.

## Límites actuales

No existen modelos de negocio, repositorios, seeds, autenticación ni acceso a
datos desde el frontend o el Agente Fitness. Tampoco se define una topología de
producción: esas decisiones pertenecen a bloques posteriores.
