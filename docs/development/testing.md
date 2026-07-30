# Pruebas y verificaciones

Todos los comandos de esta guía se ejecutan desde PowerShell y parten de la
raíz del repositorio.

## Frontend

Instala exactamente las dependencias registradas:

```powershell
Set-Location frontend
npm.cmd ci
```

Ejecuta las comprobaciones:

```powershell
npm.cmd run lint
npm.cmd run typecheck
npm.cmd run test
npm.cmd run build
```

- `lint` usa Oxlint, la herramienta incluida por la plantilla oficial actual
  de Vite.
- `typecheck` ejecuta TypeScript en modo estricto.
- `test` ejecuta Vitest y Testing Library con jsdom.
- `build` comprueba tipos y genera el bundle de Vite.

Las pruebas del frontend simulan el servicio de salud y no dependen de un
backend real.

## Backend

Sincroniza el entorno y ejecuta las comprobaciones:

```powershell
Set-Location backend
uv sync --locked
uv run ruff check .
uv run ruff format --check .
uv run mypy app tests
uv run pytest
```

Las pruebas automatizadas cubren:

- liveness sin acceso a la base;
- readiness disponible y no disponible mediante sesiones simuladas;
- contrato 200/503 sin filtrar detalles internos;
- validación y enmascarado de `DATABASE_URL`;
- cierre de la sesión entregada por la dependencia.

La suite no necesita Docker ni un PostgreSQL externo.

Si la caché global de uv no es escribible, añade `--cache-dir .uv-cache`
inmediatamente después de `uv sync` o `uv run`, por ejemplo:

```powershell
uv sync --cache-dir .uv-cache
uv run --cache-dir .uv-cache pytest
```

## Integración local con PostgreSQL

Esta verificación sí requiere Docker y parte de archivos `.env` locales
coherentes:

```powershell
docker compose --env-file .env.example config --quiet
docker compose up -d postgres
docker compose ps

Set-Location backend
uv run alembic upgrade head
uv run alembic current --check-heads
uv run alembic downgrade base
uv run alembic upgrade head
uv run alembic current --check-heads
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Con Uvicorn activo, usa otra terminal:

```powershell
$health = Invoke-WebRequest http://127.0.0.1:8000/health
$ready = Invoke-WebRequest http://127.0.0.1:8000/ready

$health.StatusCode
$health.Content
$ready.StatusCode
$ready.Content
```

Ambas rutas deben devolver 200; sus cuerpos deben ser `{"status":"ok"}` y
`{"status":"ready"}`. Detén Uvicorn con `Ctrl+C` y conserva el volumen al
detener la infraestructura:

```powershell
Set-Location ..
docker compose down
```

La eliminación deliberada de los datos se hace con
`docker compose down --volumes`; no forma parte de la verificación habitual.

## Integración continua

El workflow `CI`, definido en `.github/workflows/ci.yml`, se ejecuta cuando:

- se abre o actualiza un pull request dirigido a `main`;
- se hace push sobre `main`;
- se inicia manualmente mediante `workflow_dispatch`.

Las ejecuciones anteriores de la misma referencia se cancelan para evitar
validar commits obsoletos. El token solo dispone de `contents: read` y checkout
no persiste sus credenciales.

Se usan versiones mayores vigentes de acciones oficiales:

- `actions/checkout@v7`;
- `actions/setup-node@v7`;
- `actions/setup-python@v7`;
- `astral-sh/setup-uv@v9`.

Esta estrategia permite recibir correcciones compatibles publicadas por el
proveedor dentro de cada versión mayor. Node se fija en 24, Python en 3.12 y uv
en 0.12.0 para reproducir las versiones de herramientas elegidas por el
proyecto.

### Jobs

| Job | Validaciones | Equivalente local |
| --- | --- | --- |
| `Frontend` | Instalación bloqueada, lint, tipos, tests y build | Comandos de [Frontend](#frontend) |
| `Backend quality` | Sincronización bloqueada, Ruff, formato, mypy y pytest | Comandos de [Backend](#backend) |
| `PostgreSQL integration` | Compose, PostgreSQL, Alembic, `/health` y `/ready` | [Integración local con PostgreSQL](#integración-local-con-postgresql) |

El job de integración usa `postgres:18.4` como service container. La base,
usuario y contraseña se definen como valores efímeros exclusivos de CI y no
proceden de secretos personales. La `DATABASE_URL` solo existe en ese job.
Compose se valida sin imprimir su configuración resuelta.

El ciclo de migraciones aplica `head`, comprueba que la base esté en todas las
revisiones head, baja hasta `base` y vuelve a aplicar `head`. Después se inicia
Uvicorn de forma temporal, se esperan respuestas con reintentos acotados y se
comprueban exactamente estos contratos:

```json
{"status":"ok"}
```

```json
{"status":"ready"}
```

Un `trap` detiene Uvicorn tanto en éxito como en error. Si el servidor no llega
a responder, el job muestra un log acotado para facilitar el diagnóstico.

### Cachés

`setup-node` conserva la caché de descargas de npm y usa
`frontend/package-lock.json` como dependencia de la clave. No almacena
`node_modules`.

`setup-uv` conserva la caché propia de uv y usa `backend/uv.lock`. Los jobs
backend e integración utilizan sufijos diferentes para evitar escrituras
simultáneas sobre la misma entrada. No se cachean `.venv`, archivos `.env`,
bases de datos ni artefactos de aplicación.

### Interpretar fallos

- `Frontend`: revisa el paso concreto de lint, tipos, tests o build y reproduce
  el mismo script con npm desde `frontend`.
- `Backend quality`: reproduce el paso fallido desde `backend` después de
  `uv sync --locked`.
- `PostgreSQL integration`: distingue entre configuración Compose, arranque del
  service container, migraciones y contratos HTTP. Los logs de Uvicorn solo se
  muestran cuando ese paso falla.

### Reejecutar y proteger `main`

En GitHub, abre la pestaña **Actions**, selecciona el workflow **CI**, elige la
ejecución y usa **Re-run jobs**. `workflow_dispatch` también permite iniciar
una ejecución nueva desde **Run workflow**.

Después de una primera ejecución remota satisfactoria, la protección de `main`
debería exigir los checks:

- `Frontend`;
- `Backend quality`;
- `PostgreSQL integration`.

La configuración de branch protection no forma parte de este bloque y no se
realiza mediante la API.

## Verificación completa del bloque 2B.2

```powershell
Set-Location frontend
npm.cmd ci
npm.cmd run lint
npm.cmd run typecheck
npm.cmd run test
npm.cmd run build

Set-Location ..\backend
uv sync --locked
uv run ruff check .
uv run ruff format --check .
uv run mypy app tests
uv run pytest

Set-Location ..
docker compose --env-file .env.example config --quiet
docker compose up -d postgres
docker compose ps

Set-Location backend
uv run alembic upgrade head
uv run alembic current --check-heads
uv run alembic downgrade base
uv run alembic upgrade head
uv run alembic current --check-heads

Set-Location ..
git diff --check
git status --short --untracked-files=all
```

Además, inicia temporalmente Uvicorn y comprueba `/health` y `/ready` con el
procedimiento anterior. No dejes procesos ni contenedores activos al finalizar.

La sintaxis YAML y las comprobaciones estáticas pueden validarse localmente,
pero los disparadores, permisos efectivos, service containers y nombres
definitivos de checks solo pueden confirmarse después de ejecutar el workflow
en GitHub.
