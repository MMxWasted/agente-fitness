# Pruebas y verificaciones

Todos los comandos de esta guía se ejecutan desde PowerShell y parten de la
raíz del repositorio.

## Frontend

Instala exactamente las dependencias registradas cuando ya exista
`package-lock.json`:

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
uv run mypy
uv run pytest
```

La prueba del endpoint utiliza el cliente de pruebas de FastAPI y no necesita
servidor, base de datos ni servicios externos.

## Verificación completa del bloque 2A

Desde la raíz:

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
uv run mypy
uv run pytest

Set-Location ..
git diff --check
git status --short --untracked-files=all
```

La validación funcional adicional debe iniciar temporalmente Uvicorn, consultar
`http://127.0.0.1:8000/health`, comprobar el código 200 y el cuerpo
`{"status":"ok"}`, y detener el proceso al terminar.
