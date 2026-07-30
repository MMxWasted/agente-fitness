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
uv sync
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
docker compose config
docker compose up -d postgres
docker compose ps

Set-Location backend
uv run alembic upgrade head
uv run alembic current
uv run alembic downgrade base
uv run alembic upgrade head
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

## Verificación completa del bloque 2B.1

```powershell
Set-Location frontend
npm.cmd ci
npm.cmd run lint
npm.cmd run typecheck
npm.cmd run test
npm.cmd run build

Set-Location ..\backend
uv sync
uv run ruff check .
uv run ruff format --check .
uv run mypy app tests
uv run pytest

Set-Location ..
docker compose config
docker compose up -d postgres
docker compose ps

Set-Location backend
uv run alembic upgrade head
uv run alembic current
uv run alembic downgrade base
uv run alembic upgrade head

Set-Location ..
git diff --check
git status --short --untracked-files=all
```

Además, inicia temporalmente Uvicorn y comprueba `/health` y `/ready` con el
procedimiento anterior. No dejes procesos ni contenedores activos al finalizar.

En el entorno de creación del bloque 2B.1, las comprobaciones de Docker,
PostgreSQL y migraciones conectadas quedaron pendientes porque `docker` no
estaba instalado o publicado en `PATH`.
