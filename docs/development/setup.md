# Configuración del entorno de desarrollo

## Alcance

Esta guía cubre la fundación técnica del bloque 2A: frontend React con
TypeScript, backend FastAPI y comprobación de salud. PostgreSQL, Docker Compose
y Alembic se incorporarán en el bloque 2B.

## Requisitos

- Node.js compatible con Vite 8: 20.19 o superior, o 22.12 o superior.
- npm.
- Python 3.12 o superior.
- uv.

Versiones detectadas el 29 de julio de 2026 durante la creación del bloque:

| Herramienta | Versión detectada |
| --- | --- |
| Node.js | `v24.13.1` |
| npm | `11.8.0` |
| Python | `3.12.13` |
| uv | `0.12.0` |

En el entorno aislado de la tarea, `python` no estaba publicado en `PATH`.
Python 3.12.13 se verificó mediante el runtime local proporcionado por Codex y
uv se ejecutó contra ese intérprete de forma explícita. En un entorno normal,
uv puede localizar o administrar una versión compatible a partir de
`backend/pyproject.toml`.

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
Copy-Item frontend\.env.example frontend\.env
Copy-Item backend\.env.example backend\.env
```

El frontend utiliza:

- `VITE_API_BASE_URL`: URL base del backend.

El backend utiliza:

- `APP_NAME`: nombre mostrado en OpenAPI.
- `ENVIRONMENT`: `development`, `test` o `production`.
- `CORS_ALLOWED_ORIGINS`: lista JSON de orígenes permitidos.

Los archivos `.env` locales están ignorados por Git. Los archivos
`.env.example` no contienen secretos y sí deben permanecer versionados.

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
- Salud de la API: `http://localhost:8000/health`
- OpenAPI interactivo: `http://localhost:8000/docs`
- Esquema OpenAPI: `http://localhost:8000/openapi.json`

## Solución de problemas

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
```

### El frontend muestra «API no disponible»

Confirma que el backend está iniciado en el puerto 8000, que
`VITE_API_BASE_URL` no contiene la ruta `/health` y que el origen del frontend
está incluido en `CORS_ALLOWED_ORIGINS`.

### El puerto ya está ocupado

Detén el proceso que lo utiliza. Si cambias un puerto, actualiza también
`VITE_API_BASE_URL` o `CORS_ALLOWED_ORIGINS` según corresponda.

## Infraestructura pendiente

Este bloque no configura PostgreSQL, Docker Compose, Alembic ni infraestructura
de producción. El arranque reproducible que incluya esos componentes pertenece
al bloque 2B de la Fase 2.
