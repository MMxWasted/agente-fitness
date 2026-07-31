# Base de datos local y persistencia técnica

## Alcance

El bloque 2B.1 incorpora PostgreSQL local, conexión con SQLAlchemy 2 y
migraciones Alembic. El bloque 3A.1 añade la primera entidad persistida:
la identidad técnica `User`. El bloque 3A.2 añade `AuthSession` para renovar
y revocar sesiones web. El bloque 3B.1 añade el perfil privado `UserProfile`
sin incorporar otros dominios fitness.

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

La revisión inicial es deliberadamente vacía y conserva la línea base técnica.
La revisión `20260730_0002` crea `users` con UUID, correo único, hash de
contraseña, estado y timestamps con zona horaria. Es reversible a la revisión
anterior y no crea datos semilla. La revisión `20260730_0003` crea
`auth_sessions` con el digest único del refresh token, timestamps de creación,
actualización, expiración y revocación, índices por usuario y expiración, y
eliminación en cascada al borrar la cuenta. También es reversible y no
persiste el refresh token en claro.

La revisión `20260730_0004` crea `user_profiles` con UUID, `user_id` único,
nombre visible, fecha y altura opcionales, experiencia, zona horaria, unidades
y timestamps. La FK usa `ON DELETE CASCADE`; las restricciones `CHECK` cierran
altura, experiencia y unidades. La unicidad proporciona el índice necesario
para consultar el único perfil del usuario sin duplicar otro índice.

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

El flujo recomendado prepara configuración y dependencias, inicia PostgreSQL,
espera su healthcheck y aplica `upgrade head`:

```powershell
.\scripts\setup-dev.ps1
.\scripts\start-dev.ps1
.\scripts\check-dev.ps1
```

La alternativa manual para validar e iniciar PostgreSQL es:

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

Detener todo el entorno conservando los datos:

```powershell
.\scripts\stop-dev.ps1
```

Eliminar también el volumen local, únicamente cuando se quiera perder todos
los datos:

```powershell
.\scripts\stop-dev.ps1 -RemoveDatabaseVolume
```

El parámetro explícito es obligatorio para que el script ejecute
`docker compose down --volumes`. La parada normal nunca elimina el volumen.
Si los scripts no pueden ejecutarse, los comandos manuales equivalentes son
`docker compose down` y, para la eliminación deliberada,
`docker compose down --volumes`.

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

El job `PostgreSQL integration` validó la fundación con PostgreSQL real,
migraciones reversibles y ambos contratos mediante un service container. En
3A.1 también ejecuta la suite de usuarios y autenticación sobre la base
efímera de CI. El recorrido local completo de los scripts 2B.3 fue validado con
Docker. En 3A.2, la validación local y el job `PostgreSQL integration` del pull
request #8 cubrieron la migración de `auth_sessions`, creación, rotación,
rechazo del token anterior, revocación, caducidad, cuenta inactiva, eliminación
en cascada y concurrencia de refresh. El pull request fue fusionado en `main`.

En 3B.1, la validación local sobre PostgreSQL real cubrió la migración
reversible de `user_profiles`, tipos, restricciones, relación uno a uno,
persistencia, reemplazo idempotente, borrado en cascada, aislamiento entre
usuarios y creación concurrente. La validación remota continúa pendiente.

## Límites actuales

Solo existen los modelos, repositorios y servicios necesarios para identidad,
autenticación, gestión de sesión y perfil básico. No existen objetivos,
equipamiento, preferencias, limitaciones, historial corporal, otras entidades
fitness, seeds ni Agente Fitness. Tampoco se define una topología de
producción: esas decisiones pertenecen a bloques posteriores.
