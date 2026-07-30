# Configuración del entorno de desarrollo

## Alcance

Esta guía cubre la fundación técnica y los bloques 3A.1 y 3A.2: frontend React con
TypeScript, backend FastAPI, PostgreSQL local mediante Docker Compose, scripts
PowerShell, identidad de usuario, autenticación bearer y sesión web renovable.
Las únicas entidades persistidas son `User` y `AuthSession`; todavía no existen
datos fitness.

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
| Docker | Disponible y validado en el recorrido local del bloque 2B.3 |
| Docker Compose | Disponible y validado en el recorrido local del bloque 2B.3 |

En el entorno aislado de estas tareas, `python` no estaba publicado en `PATH`.
Python 3.12.13 se verificó mediante el runtime local proporcionado por Codex y
uv se ejecutó contra ese intérprete de forma explícita. En un entorno normal,
uv puede localizar o administrar una versión compatible a partir de
`backend/pyproject.toml`.

La integración real con PostgreSQL, Alembic, `/health` y `/ready` fue validada
tanto por el workflow de GitHub Actions como mediante el recorrido local
completo de los scripts con Docker.

## Preparación recomendada

Desde la raíz del repositorio:

```powershell
.\scripts\setup-dev.ps1
```

El script comprueba Git, Docker, Docker Compose, Node.js, npm y uv. Después crea
los archivos `.env` que falten, genera criptográficamente
`JWT_SECRET_KEY` si falta o conserva el marcador público del ejemplo, ejecuta
`npm.cmd ci` y sincroniza el backend con `uv sync --locked`. Conserva las demás
variables existentes, no muestra el secreto, no instala herramientas globales
ni modifica lockfiles.

Si la política local impide ejecutar archivos `.ps1`, usa un proceso aislado
sin cambiar la política del sistema:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup-dev.ps1
```

Repetir el script conserva la configuración local y los datos existentes.

### Preparación manual

Si el script falla, ejecuta los pasos equivalentes:

```powershell
if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
}
if (-not (Test-Path frontend\.env)) {
    Copy-Item frontend\.env.example frontend\.env
}
if (-not (Test-Path backend\.env)) {
    Copy-Item backend\.env.example backend\.env
}

Set-Location frontend
npm.cmd ci

Set-Location ..\backend
uv sync --locked

Set-Location ..
```

No reemplaces un `.env` con configuración local.

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
- `BACKEND_PORT`: puerto local de FastAPI usado por los scripts, 8000 por
  defecto.
- `FRONTEND_PORT`: puerto local de Vite usado por los scripts, 5173 por
  defecto.

Los `.env` creados antes de 2B.3 pueden no contener los dos últimos campos. En
ese caso los scripts conservan compatibilidad usando 8000 y 5173; puedes
añadirlos explícitamente cuando necesites cambiar esos puertos.

El frontend utiliza `VITE_API_BASE_URL` como URL base del backend.

El backend utiliza:

- `APP_NAME`: nombre mostrado en OpenAPI.
- `ENVIRONMENT`: `development`, `test` o `production`.
- `CORS_ALLOWED_ORIGINS`: lista JSON de orígenes permitidos.
- `DATABASE_URL`: URL completa con esquema `postgresql+psycopg`.
- `DATABASE_CONNECT_TIMEOUT_SECONDS`: espera máxima inicial por PostgreSQL,
  entre 1 y 30 segundos.
- `JWT_SECRET_KEY`: secreto de firma con un mínimo de 32 bytes. El ejemplo es
  únicamente un marcador local y `setup-dev.ps1` lo sustituye por un valor
  aleatorio en `backend\.env`.
- `JWT_ALGORITHM`: algoritmo permitido; en esta fase solo se admite `HS256`.
- `ACCESS_TOKEN_EXPIRE_MINUTES`: vigencia del access token, 30 minutos por
  defecto y entre 5 y 1440.
- `REFRESH_TOKEN_EXPIRE_DAYS`: vigencia absoluta de la sesión renovable, 7
  días por defecto y entre 1 y 90.
- `REFRESH_COOKIE_NAME`: nombre de la cookie `HttpOnly` que transporta el
  refresh token.
- `REFRESH_COOKIE_SECURE`: exige HTTPS para la cookie; debe ser `true` en
  producción.
- `REFRESH_COOKIE_SAMESITE`: política `lax` o `strict`; nunca `none` en esta
  fase.
- `REFRESH_COOKIE_DOMAIN`: dominio opcional. Vacío conserva una cookie
  host-only, que es la opción local recomendada.
- `REFRESH_COOKIE_PATH`: limitado por defecto a `/api/v1/auth`.
- `CSRF_TRUSTED_ORIGINS`: lista JSON de orígenes autorizados para operaciones
  de sesión basadas en cookie; debe ser un subconjunto de
  `CORS_ALLOWED_ORIGINS`.

El entorno `production` rechaza explícitamente el marcador local documentado.
No reutilices el secreto de desarrollo en otro entorno ni lo incluyas en
comandos, logs o documentación.

Si cambias usuario, contraseña, puerto o nombre de base en el `.env` de la
raíz, actualiza de forma coherente `DATABASE_URL` en `backend\.env`. No uses
las credenciales de ejemplo fuera del desarrollo local.

Si cambias `BACKEND_PORT`, actualiza también `VITE_API_BASE_URL`. Si cambias
`FRONTEND_PORT`, actualiza `CORS_ALLOWED_ORIGINS` para conservar la comunicación
entre frontend y backend.

Los archivos `.env` locales están ignorados por Git. Los archivos
`.env.example` no contienen secretos reales y sí deben permanecer versionados.

## Flujo habitual

Después de la preparación:

```powershell
.\scripts\start-dev.ps1
.\scripts\check-dev.ps1
```

`start-dev.ps1` valida la configuración, inicia solo PostgreSQL con Compose,
espera su healthcheck, aplica `alembic upgrade head`, inicia FastAPI, comprueba
`/health` y `/ready`, inicia Vite y espera una respuesta HTTP. Los reintentos
son acotados y un fallo revierte únicamente los procesos iniciados por esa
ejecución.

`check-dev.ps1` muestra Docker, PostgreSQL, procesos gestionados, `/health`,
`/ready`, frontend y revisión Alembic. Devuelve código distinto de cero cuando
el entorno completo no está disponible.

Los procesos del backend y frontend se ejecutan ocultos y sus logs se guardan
en:

```text
.dev-state/logs/backend.stdout.log
.dev-state/logs/backend.stderr.log
.dev-state/logs/frontend.stdout.log
.dev-state/logs/frontend.stderr.log
```

El directorio `.dev-state/` está ignorado por Git y no contiene configuración
ni credenciales. Cada proceso se registra mediante PID y hora de inicio para no
confundirlo con un PID reutilizado.

## Inicio manual de PostgreSQL

Desde la raíz:

```powershell
docker compose config
docker compose up -d postgres
docker compose ps
```

El servicio se llama `postgres`, utiliza la imagen oficial `postgres:18.4`,
publica el puerto configurado y conserva los datos en el volumen nombrado
`agente_fitness_postgres_data`.

## Aplicación manual de migraciones

```powershell
Set-Location backend
uv run alembic upgrade head
uv run alembic current
Set-Location ..
```

La revisión inicial conserva la línea base técnica vacía. La revisión
`20260730_0002` crea exclusivamente la tabla `users` y sus restricciones. La
revisión `20260730_0003` añade `auth_sessions`, sin datos fitness ni semillas.

## Inicio manual del backend

En una terminal PowerShell:

```powershell
Set-Location backend
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Inicio manual del frontend

En otra terminal PowerShell:

```powershell
Set-Location frontend
npm.cmd run dev -- --host 127.0.0.1
```

## URLs locales

- Aplicación: `http://localhost:5173`
- Liveness de la API: `http://localhost:8000/health`
- Readiness de la API: `http://localhost:8000/ready`
- Registro: `POST http://localhost:8000/api/v1/auth/register`
- Inicio de sesión: `POST http://localhost:8000/api/v1/auth/token`
- Renovación: `POST http://localhost:8000/api/v1/auth/refresh`
- Cierre de sesión: `POST http://localhost:8000/api/v1/auth/logout`
- Usuario actual: `GET http://localhost:8000/api/v1/users/me`
- OpenAPI interactivo: `http://localhost:8000/docs`
- Esquema OpenAPI: `http://localhost:8000/openapi.json`

`GET /health` confirma que el proceso FastAPI responde y no consulta la base.
`GET /ready` ejecuta `SELECT 1`: devuelve 200 cuando PostgreSQL responde y 503
con un contrato controlado cuando no está disponible.

El registro recibe JSON. El endpoint de token recibe formulario OAuth2:
`username` es el campo técnico que contiene el correo. Las contraseñas admiten
entre 15 y 128 caracteres, sin reglas arbitrarias de composición. El access
token se usa en el encabezado `Authorization: Bearer` y el frontend lo conserva
exclusivamente en memoria. El login también crea una cookie de refresh
`HttpOnly`; el frontend la envía con credenciales únicamente a login, refresh
y logout. Refresh y logout requieren que el navegador proporcione un
encabezado `Origin` incluido en `CSRF_TRUSTED_ORIGINS`.

## Detener el entorno

La parada recomendada detiene únicamente los árboles de procesos registrados y
después ejecuta `docker compose down`:

```powershell
.\scripts\stop-dev.ps1
```

Es segura si alguno de los componentes ya está detenido y conserva tanto los
logs como el volumen `agente_fitness_postgres_data`. La eliminación de todos
los datos requiere el parámetro inequívoco:

```powershell
.\scripts\stop-dev.ps1 -RemoveDatabaseVolume
```

La alternativa manual desde la raíz es:

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

`setup-dev.ps1` y `start-dev.ps1` se detienen con un mensaje claro antes de
iniciar servicios cuando falta Docker. `check-dev.ps1` representa ese estado
como desconocido.

### PostgreSQL no alcanza el estado healthy

Ejecuta `docker compose ps` y `docker compose logs postgres`. Comprueba que el
puerto no esté ocupado y que las cuatro variables `POSTGRES_*` sean válidas.
No copies logs que puedan contener información sensible.

El script de arranque muestra automáticamente `docker compose ps` y las últimas
50 líneas del servicio antes de detenerse.

### `/ready` devuelve 503

Confirma que el contenedor está healthy, que se aplicaron las migraciones y que
`backend\.env` contiene una `DATABASE_URL` coherente con el `.env` de la raíz.
El 503 no afecta al contrato de liveness de `/health`.

### El backend indica que falta `JWT_SECRET_KEY`

Vuelve a ejecutar `.\scripts\setup-dev.ps1`. En un `backend\.env` anterior a
3A.1, el script añade un secreto local aleatorio sin mostrarlo ni cambiar la
URL de PostgreSQL. Si configuras el backend manualmente, define un valor de al
menos 32 bytes y no uses el marcador local en producción.

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

### La sesión no se restaura o refresh/logout devuelve 403

Comprueba que el origen exacto del frontend aparece tanto en
`CORS_ALLOWED_ORIGINS` como en `CSRF_TRUSTED_ORIGINS`. En desarrollo,
`localhost` y `127.0.0.1` son orígenes distintos. Verifica también que el
navegador acepta la cookie, que `REFRESH_COOKIE_PATH` conserva
`/api/v1/auth` y que `REFRESH_COOKIE_SECURE=false` solo mientras uses HTTP
local. No copies el refresh token a JavaScript, logs ni almacenamiento web.

### El puerto ya está ocupado

Detén el proceso que lo utiliza o cambia `POSTGRES_PORT`. Si cambias un puerto,
actualiza también `DATABASE_URL`, `VITE_API_BASE_URL` o
`CORS_ALLOWED_ORIGINS`, según corresponda.

Los scripts no terminan procesos ajenos. Si `BACKEND_PORT` o `FRONTEND_PORT`
está ocupado sin un registro válido en `.dev-state/`, el arranque falla y pide
liberar o reconfigurar el puerto.

### Entorno parcialmente iniciado

Ejecuta primero:

```powershell
.\scripts\check-dev.ps1
.\scripts\stop-dev.ps1
```

La parada elimina registros PID obsoletos sin matar el proceso que haya
reutilizado ese PID. Después puedes repetir `start-dev.ps1`. Si una ventana de
PowerShell se cierra de forma forzada justo durante el arranque, revisa los
logs y el estado antes de intervenir manualmente.

### Consultar logs

```powershell
Get-Content .dev-state\logs\backend.stderr.log -Tail 50
Get-Content .dev-state\logs\frontend.stderr.log -Tail 50
```

Los logs se reinician al volver a iniciar cada proceso y se conservan durante
la parada normal.

## Infraestructura pendiente

Docker Compose solo administra PostgreSQL local. Los contenedores de frontend y
backend y la infraestructura de producción siguen fuera de este bloque. El
recorrido local completo de 2B.3 fue validado correctamente. La validación
remota de 3A.1 también finalizó correctamente en el pull request #6 mediante
los jobs `Frontend`, `Backend quality` y `PostgreSQL integration`. La sesión
web renovable de 3A.2 fue validada localmente y por esos mismos tres jobs en el
pull request #8, ya fusionado en `main`; no queda validación remota pendiente
para el bloque. Proveedores de identidad externos, perfil fitness y demás
datos de negocio pertenecen a bloques posteriores.
