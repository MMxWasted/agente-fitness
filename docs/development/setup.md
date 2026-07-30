# Configuración del entorno de desarrollo

## Alcance

Esta guía cubre la fundación técnica disponible hasta el bloque 2B.1:
frontend React con TypeScript, backend FastAPI y PostgreSQL local mediante
Docker Compose. La persistencia incluida es únicamente técnica; todavía no
existen modelos ni datos de negocio.

## Requisitos

- Node.js compatible con Vite 8: 20.19 o superior, o 22.12 o superior.
- npm.
- Python 3.12 o superior.
- uv.
- Docker Desktop o Docker Engine con Docker Compose v2.

Versiones detectadas durante los bloques de fundación:

| Herramienta | Versión detectada |
| --- | --- |
| Node.js | `v24.13.1` (bloque 2A, 29 de julio de 2026) |
| npm | `11.8.0` (bloque 2A, 29 de julio de 2026) |
| Python | `3.12.13` (bloque 2B.1, 30 de julio de 2026) |
| uv | `0.12.0` (bloque 2B.1, 30 de julio de 2026) |
| Docker | No disponible en el entorno de verificación del bloque 2B.1 |
| Docker Compose | No disponible en el entorno de verificación del bloque 2B.1 |

En el entorno aislado de estas tareas, `python` no estaba publicado en `PATH`.
Python 3.12.13 se verificó mediante el runtime local proporcionado por Codex y
uv se ejecutó contra ese intérprete de forma explícita. En un entorno normal,
uv puede localizar o administrar una versión compatible a partir de
`backend/pyproject.toml`.

La configuración y las pruebas sin servicios externos sí se verificaron. Los
comandos que requieren Docker y PostgreSQL deben ejecutarse manualmente en un
equipo que cumpla esos requisitos.

## Instalar dependencias

Desde la raíz del repositorio, en PowerShell:

```powershell
Set-Location frontend
npm.cmd install

Set-Location ..\backend
uv sync

Set-Location ..
```

Se usa `npm.cmd` para evitar que una política de ejecución de PowerShell
bloquee el wrapper `npm.ps1`.

## Configurar variables de entorno

Crea archivos locales a partir de los ejemplos:

```powershell
Copy-Item .env.example .env
Copy-Item frontend\.env.example frontend\.env
Copy-Item backend\.env.example backend\.env
```

El archivo `.env` de la raíz configura el servicio PostgreSQL:

- `POSTGRES_DB`: nombre de la base local.
- `POSTGRES_USER`: usuario local.
- `POSTGRES_PASSWORD`: contraseña exclusiva del entorno local.
- `POSTGRES_PORT`: puerto publicado en el host.

El frontend utiliza `VITE_API_BASE_URL` como URL base del backend.

El backend utiliza:

- `APP_NAME`: nombre mostrado en OpenAPI.
- `ENVIRONMENT`: `development`, `test` o `production`.
- `CORS_ALLOWED_ORIGINS`: lista JSON de orígenes permitidos.
- `DATABASE_URL`: URL completa con esquema `postgresql+psycopg`.
- `DATABASE_CONNECT_TIMEOUT_SECONDS`: espera máxima inicial por PostgreSQL,
  entre 1 y 30 segundos.

Si cambias usuario, contraseña, puerto o nombre de base en el `.env` de la
raíz, actualiza de forma coherente `DATABASE_URL` en `backend\.env`. No uses
las credenciales de ejemplo fuera del desarrollo local.

Los archivos `.env` locales están ignorados por Git. Los archivos
`.env.example` no contienen secretos reales y sí deben permanecer versionados.

## Iniciar PostgreSQL

Desde la raíz:

```powershell
docker compose config
docker compose up -d postgres
docker compose ps
```

El servicio se llama `postgres`, utiliza la imagen oficial `postgres:18.4`,
publica el puerto configurado y conserva los datos en el volumen nombrado
`agente_fitness_postgres_data`.

## Aplicar migraciones

```powershell
Set-Location backend
uv run alembic upgrade head
uv run alembic current
Set-Location ..
```

La revisión inicial es una línea base técnica vacía. Alembic administra su
tabla de versión, pero todavía no crea tablas de negocio.

## Iniciar el backend

En una terminal PowerShell:

```powershell
Set-Location backend
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Iniciar el frontend

En otra terminal PowerShell:

```powershell
Set-Location frontend
npm.cmd run dev -- --host 127.0.0.1
```

## URLs locales

- Aplicación: `http://localhost:5173`
- Liveness de la API: `http://localhost:8000/health`
- Readiness de la API: `http://localhost:8000/ready`
- OpenAPI interactivo: `http://localhost:8000/docs`
- Esquema OpenAPI: `http://localhost:8000/openapi.json`

`GET /health` confirma que el proceso FastAPI responde y no consulta la base.
`GET /ready` ejecuta `SELECT 1`: devuelve 200 cuando PostgreSQL responde y 503
con un contrato controlado cuando no está disponible.

## Detener PostgreSQL

Desde la raíz:

```powershell
docker compose down
```

Este comando detiene y elimina el contenedor y la red, pero conserva el
volumen. Para borrar deliberadamente todos los datos locales:

```powershell
docker compose down --volumes
```

La segunda operación es destructiva y no se debe usar como parada habitual.

## Solución de problemas

### Docker no está disponible

Comprueba:

```powershell
docker --version
docker compose version
```

Instala o inicia Docker fuera de este repositorio antes de continuar. Esta guía
no instala herramientas globales ni modifica la configuración del sistema.

### PostgreSQL no alcanza el estado healthy

Ejecuta `docker compose ps` y `docker compose logs postgres`. Comprueba que el
puerto no esté ocupado y que las cuatro variables `POSTGRES_*` sean válidas.
No copies logs que puedan contener información sensible.

### `/ready` devuelve 503

Confirma que el contenedor está healthy, que se aplicaron las migraciones y que
`backend\.env` contiene una `DATABASE_URL` coherente con el `.env` de la raíz.
El 503 no afecta al contrato de liveness de `/health`.

### PowerShell bloquea npm.ps1

Usa `npm.cmd` en lugar de `npm`. No es necesario cambiar la política de
ejecución del sistema.

### uv no encuentra Python

Comprueba una instalación compatible con `python --version`. uv también puede
administrar Python; consulta `uv python list` antes de instalar o cambiar una
versión.

### uv informa de «Acceso denegado» en la caché o `.venv`

Comprueba que no queden procesos Python usando el entorno y que OneDrive u otro
sincronizador no mantenga los archivos bloqueados. En un entorno restringido se
puede usar una caché local, ya ignorada por Git:

```powershell
Set-Location backend
uv sync --cache-dir .uv-cache
uv run --cache-dir .uv-cache pytest
```

### El frontend muestra «API no disponible»

Confirma que el backend está iniciado en el puerto 8000, que
`VITE_API_BASE_URL` no contiene la ruta `/health` y que el origen del frontend
está incluido en `CORS_ALLOWED_ORIGINS`.

### El puerto ya está ocupado

Detén el proceso que lo utiliza o cambia `POSTGRES_PORT`. Si cambias un puerto,
actualiza también `DATABASE_URL`, `VITE_API_BASE_URL` o
`CORS_ALLOWED_ORIGINS`, según corresponda.

## Infraestructura pendiente

Docker Compose solo administra PostgreSQL local. Los contenedores de frontend y
backend y la infraestructura de producción siguen fuera de este bloque. La
integración continua ya está configurada, pero debe validarse mediante una
ejecución remota satisfactoria en GitHub.
