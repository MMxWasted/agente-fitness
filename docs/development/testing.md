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

Las pruebas del frontend simulan los servicios de salud, autenticación, perfil
e historial XLSX; no dependen de un backend real. Cubren renderizado,
disponibilidad de la API, login correcto e incorrecto, restauración y
expiración de sesión, fallos de red, logout, perfil, selección y validación del
archivo, análisis, agrupación por revisión y categoría, advertencias, errores
bloqueantes, métricas desconocidas, reintento y cambio de archivo. También
comprueban fuentes, decisiones, plan, confirmación, historial, detalle y
reversión, y que el access token, el `File` y la clave idempotente no se
persisten en Web Storage ni se representa el token en el DOM.

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
- cierre de la sesión entregada por la dependencia;
- normalización de correo, duplicados y condición de carrera;
- creación y verificación de hashes Argon2id;
- emisión y validación de JWT, incluida expiración, firma y claims;
- configuración y enmascarado del secreto;
- registro, login, usuario actual y errores genéricos sin exponer el hash;
- tokens ausentes, inválidos o de identidades inexistentes e inactivas;
- generación y digest de refresh tokens opacos;
- atributos y borrado de la cookie `HttpOnly`;
- validación de orígenes frente a CSRF;
- creación, rotación, revocación, caducidad y limpieza de sesiones;
- validación, normalización y contrato del perfil fitness básico;
- creación, consulta, reemplazo idempotente y borrado de valores opcionales
  del perfil;
- autenticación, usuario inactivo, aislamiento entre propietarios y
  resolución controlada de creaciones concurrentes del perfil;
- estructura del fixture XLSX, rangos combinados, secciones y revisiones;
- fechas completas o sin año, `Decimal` con coma o punto, vacío frente a cero,
  unidades, alias y lateralidad;
- métricas desconocidas, fórmulas, booleanos, NaN, infinito y rangos básicos;
- tamaño, extensión, MIME, firma y estructura ZIP/OOXML, entradas, tamaño
  descomprimido, rutas, cifrado, protección y XML inseguro;
- estabilidad y sensibilidad del fingerprint;
- contrato bearer multipart, 401, 403, 413, 415 y 422 sin datos arbitrarios,
  `user_id`, tokens ni persistencia.

La suite no necesita Docker ni un PostgreSQL externo.

Si la caché global de uv no es escribible, añade `--cache-dir .uv-cache`
inmediatamente después de `uv sync` o `uv run`, por ejemplo:

```powershell
uv sync --cache-dir .uv-cache
uv run --cache-dir .uv-cache pytest
```

## Scripts de entorno local

La lógica reutilizable de los scripts se comprueba sin Pester ni dependencias
adicionales:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\test-dev-scripts.ps1
```

Estas pruebas usan un directorio temporal aislado y cubren:

- creación de un `.env` inexistente;
- conservación de un `.env` existente;
- generación criptográfica y conservación posterior del secreto JWT local;
- lectura de variables y valores entre comillas;
- valores predeterminados y validación de puertos;
- citado de argumentos y rechazo de metacaracteres del shell;
- captura separada de `stdout`, `stderr` y código de salida de procesos nativos;
- `stderr` informativo con código cero y fallos nativos controlados;
- normalización del JSON vacío, único, múltiple o nulo de Docker Compose;
- ausencia controlada del contenedor PostgreSQL y de archivos PID;
- mensajes con acentos y UTF-8 con BOM en Windows PowerShell 5.1;
- comprobación de PID junto con su hora de inicio;
- rechazo de un PID reutilizado;
- detección no destructiva de un puerto ocupado.

La sintaxis de todos los scripts puede validarse con el parser incluido en
PowerShell, sin instalar herramientas:

```powershell
$failed = $false
Get-ChildItem scripts -Filter *.ps1 | ForEach-Object {
    $tokens = $null
    $errors = $null
    [void][System.Management.Automation.Language.Parser]::ParseFile(
        $_.FullName,
        [ref]$tokens,
        [ref]$errors
    )
    if ($errors.Count -gt 0) {
        $failed = $true
        $errors
    }
}
if ($failed) {
    throw 'Existen errores de sintaxis PowerShell.'
}
```

## Integración local con PostgreSQL

Estas pruebas usan PostgreSQL real, pero rechazan la base local normal. El
nombre de la base debe terminar en `_test` o `_ci`. Inicia el contenedor y crea
una base de test separada, de forma idempotente:

```powershell
docker compose --env-file .env.example config --quiet
docker compose up -d postgres
docker compose ps

$postgresUser = (
    docker compose exec -T postgres printenv POSTGRES_USER
).Trim()
$testDatabase = 'agente_fitness_test'
$exists = (
    docker compose exec -T postgres psql `
        -U $postgresUser `
        -d postgres `
        -tAc "SELECT 1 FROM pg_database WHERE datname='$testDatabase'"
).Trim()
if ($exists -ne '1') {
    docker compose exec -T postgres createdb `
        -U $postgresUser `
        $testDatabase
}
```

Exporta una configuración exclusiva de test. Esta URL usa los valores públicos
de `.env.example`; si cambiaste las credenciales o el puerto local, adapta solo
esta variable:

```powershell
$env:ENVIRONMENT = 'test'
$env:DATABASE_URL = (
    'postgresql+psycopg://agente_fitness:change_me_local_only' +
    '@localhost:5432/agente_fitness_test'
)
$env:JWT_SECRET_KEY = (
    'integration-test-only-secret-that-is-at-least-32-bytes'
)
$env:CORS_ALLOWED_ORIGINS = '["http://localhost:5173"]'
$env:CSRF_TRUSTED_ORIGINS = '["http://localhost:5173"]'

Set-Location backend
uv run alembic upgrade head
uv run alembic current
uv run alembic downgrade -1
uv run alembic upgrade head
uv run alembic current
uv run pytest integration_tests -m integration
```

La suite crea correos únicos, elimina exclusivamente sus propios usuarios y
sesiones, y comprueba el esquema PostgreSQL, la revisión Alembic, registro,
persistencia, hash, duplicado, login, `/users/me`, cuentas inactivas, tokens
inválidos y los contratos de `/health` y `/ready`. Para 3A.2 añade creación,
rotación, rechazo del refresh anterior, revocación, caducidad, eliminación en
cascada y la garantía de un único ganador ante refresh concurrente. Para
3B.1 añade el esquema y las restricciones de `user_profiles`, persistencia,
actualización, relación uno a uno, aislamiento, borrado en cascada y creación
concurrente.

Para el recorrido HTTP manual, conserva esas variables y ejecuta en una
terminal:

```powershell
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

En otra terminal con la misma configuración:

```powershell
$baseUrl = 'http://127.0.0.1:8000'
$email = "manual-$([guid]::NewGuid().ToString('N'))@example.com"
$passwordBytes = New-Object byte[] 32
$passwordGenerator = (
    [System.Security.Cryptography.RandomNumberGenerator]::Create()
)
try {
    $passwordGenerator.GetBytes($passwordBytes)
}
finally {
    $passwordGenerator.Dispose()
}
$password = [Convert]::ToBase64String($passwordBytes)
$registration = @{
    email = $email
    password = $password
} | ConvertTo-Json

$registered = Invoke-RestMethod `
    -Method Post `
    -Uri "$baseUrl/api/v1/auth/register" `
    -ContentType 'application/json' `
    -Body $registration

$tokenResponse = Invoke-RestMethod `
    -Method Post `
    -Uri "$baseUrl/api/v1/auth/token" `
    -ContentType 'application/x-www-form-urlencoded' `
    -Headers @{ Origin = 'http://localhost:5173' } `
    -Body @{ username = $email; password = $password } `
    -SessionVariable browserSession

$currentUser = Invoke-RestMethod `
    -Method Get `
    -Uri "$baseUrl/api/v1/users/me" `
    -Headers @{ Authorization = "Bearer $($tokenResponse.access_token)" }

$refreshed = Invoke-RestMethod `
    -Method Post `
    -Uri "$baseUrl/api/v1/auth/refresh" `
    -Headers @{ Origin = 'http://localhost:5173' } `
    -WebSession $browserSession

$loggedOut = Invoke-WebRequest `
    -Method Post `
    -Uri "$baseUrl/api/v1/auth/logout" `
    -Headers @{ Origin = 'http://localhost:5173' } `
    -WebSession $browserSession

$registered
$currentUser
$loggedOut.StatusCode
```

No escribas `$tokenResponse`, `$refreshed` ni la cookie en consola. El resultado
de logout debe ser 204. La cookie rotada anterior debe dejar de ser válida y la
cookie revocada no debe renovar la sesión. Repite el registro para obtener 409
y prueba una contraseña o token incorrectos para obtener 401. Las respuestas
públicas no deben contener `password`, `password_hash`, refresh tokens ni sus
digests.

Detén Uvicorn con `Ctrl+C`, elimina las variables del proceso y conserva el
volumen al detener la infraestructura:

```powershell
Set-Location ..
Remove-Item Env:ENVIRONMENT
Remove-Item Env:DATABASE_URL
Remove-Item Env:JWT_SECRET_KEY
Remove-Item Env:CORS_ALLOWED_ORIGINS
Remove-Item Env:CSRF_TRUSTED_ORIGINS
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
| `PostgreSQL integration` | Compose, PostgreSQL, Alembic, autenticación, sesiones, perfiles e historial corporal reales, `/health` y `/ready` | [Integración local con PostgreSQL](#integración-local-con-postgresql) |

Los tres jobs mantienen los nombres `Frontend`, `Backend quality` y
`PostgreSQL integration`. La fundación 2B ya fue validada en GitHub. En el
pull request #6 del bloque 3A.1, `Frontend`, `Backend quality` y
`PostgreSQL integration` finalizaron correctamente; el tercero incluyó la
suite real de usuarios y autenticación sobre PostgreSQL.

En el pull request #8 del bloque 3A.2, esos mismos tres jobs finalizaron
correctamente. `PostgreSQL integration` incluyó la migración y la suite real
de sesiones sobre PostgreSQL. El pull request fue fusionado en `main`, por lo
que no queda validación remota pendiente para 3A.2.

En el pull request #12 del bloque 3B.2A, `Frontend`, `Backend quality` y
`PostgreSQL integration` finalizaron correctamente. El adaptador V1 también se
contrastó con una copia anonimizada que conserva la estructura técnica del
Excel real. El pull request fue fusionado en `main`; no queda validación
remota ni funcional pendiente para 3B.2A.

3B.2B está implementado y validado localmente. Su validación en los jobs
`Frontend`, `Backend quality` y `PostgreSQL integration` permanece pendiente
hasta ejecutar el pull request de este bloque.

El job de integración usa `postgres:18.4` como service container. La base,
usuario y contraseña se definen como valores efímeros exclusivos de CI y no
proceden de secretos personales. La `DATABASE_URL` solo existe en ese job.
Compose se valida sin imprimir su configuración resuelta.

El ciclo de migraciones aplica `head`, comprueba que la base esté en todas las
revisiones head, baja hasta `base` y vuelve a aplicar `head`. A continuación
ejecuta las pruebas PostgreSQL con una base efímera `_ci`. Después se inicia
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

La protección de `main` debería exigir los checks ya validados:

- `Frontend`;
- `Backend quality`;
- `PostgreSQL integration`.

La configuración de branch protection no forma parte de este bloque y no se
realiza mediante la API.

## Verificación completa del bloque 2B.3

```powershell
Set-Location .
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\test-dev-scripts.ps1

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

.\scripts\setup-dev.ps1
.\scripts\start-dev.ps1
.\scripts\check-dev.ps1

$health = Invoke-WebRequest http://127.0.0.1:8000/health
$ready = Invoke-WebRequest http://127.0.0.1:8000/ready
$frontend = Invoke-WebRequest http://127.0.0.1:5173

.\scripts\stop-dev.ps1
git diff --check
git status --short --untracked-files=all
```

La parada normal debe dejar el volumen
`agente_fitness_postgres_data` existente. No pruebes
`-RemoveDatabaseVolume` sobre datos que deban conservarse; utiliza un entorno
temporal controlado si necesitas verificar esa ruta destructiva.

### Escenarios manuales de 2B.3

| Escenario | Resultado esperado |
| --- | --- |
| Preparación limpia | Crea solo los `.env` ausentes, ejecuta instalaciones bloqueadas y no sobrescribe configuración |
| Arranque normal | PostgreSQL healthy, migraciones en head, contratos HTTP correctos y frontend accesible |
| Arranque repetido | Reconoce los PID registrados y no crea duplicados |
| Parada normal | Detiene solo procesos gestionados, ejecuta Compose down y conserva el volumen |
| Parada repetida | Informa de servicios no iniciados sin matar procesos ajenos |
| Error de PostgreSQL | Se detiene antes de FastAPI y Vite y muestra estado y logs acotados |
| Puerto ocupado | Falla con un mensaje útil y no termina el proceso propietario |
| Persistencia | El volumen continúa tras reiniciar y solo se elimina con `-RemoveDatabaseVolume` |

La validación local completa de 2B.3 finalizó correctamente. Se comprobaron:

- la preparación sin sobrescribir los archivos `.env` existentes;
- el arranque inicial de PostgreSQL, FastAPI y Vite;
- el arranque repetido sin crear procesos duplicados;
- la parada normal y el estado detenido controlado de todos los componentes;
- un segundo arranque completo usando el volumen PostgreSQL existente;
- la revisión actual de Alembic en `head`;
- los contratos HTTP de `/health`, `/ready` y el frontend;
- la persistencia de `agente_fitness_postgres_data` después de la parada y el
  reinicio.

La parada final y su repetición no dejaron listeners en los puertos 8000 o
5173 ni archivos PID gestionados activos.

## Verificación completa del bloque 3A.1

Ejecuta los comandos del bloque base y añade la base PostgreSQL específica de
test descrita en [Integración local con PostgreSQL](#integración-local-con-postgresql):

```powershell
Set-Location .
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\test-dev-scripts.ps1

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

# Con ENVIRONMENT, DATABASE_URL de test y JWT_SECRET_KEY definidos:
uv run alembic upgrade head
uv run alembic current
uv run alembic downgrade -1
uv run alembic upgrade head
uv run alembic current
uv run pytest integration_tests -m integration

Set-Location ..
docker compose --env-file .env.example config
git status
git diff --stat
git diff --check
```

La verificación manual adicional debe recorrer registro 201, duplicado 409,
login correcto, credenciales incorrectas 401, `/users/me` correcto, petición
sin token, token inválido y ausencia de `password_hash`. El entorno se detiene
con `.\scripts\stop-dev.ps1`; la parada normal conserva el volumen PostgreSQL.

## Verificación completa del bloque 3A.2

Ejecuta todas las comprobaciones de calidad y la integración PostgreSQL sobre
una base exclusiva `_test` o `_ci`:

```powershell
Set-Location frontend
npm.cmd ci
npm.cmd run lint
npm.cmd run typecheck
npm.cmd run test
npm.cmd run build

Set-Location ..\backend
uv sync --locked
uv lock --check
uv run ruff check .
uv run ruff format --check .
uv run mypy app tests
uv run pytest

# Con las variables de integración definidas como en la sección anterior:
uv run alembic upgrade head
uv run alembic current --check-heads
uv run alembic downgrade -1
uv run alembic upgrade head
uv run alembic current --check-heads
uv run alembic check
uv run pytest integration_tests -m integration

Set-Location ..
git diff --check
git status --short --untracked-files=all
```

La revisión manual y automatizada debe confirmar:

- login y restauración de sesión sin guardar el access token en almacenamiento
  persistente del navegador;
- cookie de refresh `HttpOnly`, rotatoria, con expiración absoluta y atributos
  coherentes con el entorno;
- rechazo de refresh ausente, caducado, revocado, reutilizado o asociado a una
  cuenta inactiva;
- logout 204 idempotente que revoca la sesión y elimina la cookie;
- rechazo 403 de refresh/logout cuando falta un `Origin` confiable;
- protección CORS con credenciales solo para orígenes explícitos;
- migración 3A.2 reversible, en `head` y sin cambios de esquema pendientes;
- ausencia de secretos, tokens o digests en respuestas, logs, DOM y Git.

## Verificación completa del bloque 3B.1

Ejecuta todas las comprobaciones de calidad y la integración PostgreSQL sobre
una base exclusiva con sufijo `_test` o `_ci`:

```powershell
Set-Location frontend
npm.cmd ci
npm.cmd run lint
npm.cmd run typecheck
npm.cmd run test
npm.cmd run build

Set-Location ..\backend
uv sync --locked
uv lock --check
uv run ruff check .
uv run ruff format --check .
uv run mypy app tests
uv run pytest

# Con las variables de integración definidas como en la sección anterior:
uv run alembic upgrade head
uv run alembic current --check-heads
uv run alembic downgrade -1
uv run alembic upgrade head
uv run alembic current --check-heads
uv run alembic check
uv run pytest integration_tests -m integration

Set-Location ..
git diff --check
git status --short --untracked-files=all
```

La validación local de 3B.1 finalizó correctamente con 111 pruebas backend,
26 pruebas frontend y 11 pruebas de integración sobre PostgreSQL real. El
ciclo de migración aplicó `head`, bajó de `20260730_0004` a
`20260730_0003`, volvió a aplicar `head`, confirmó todas las revisiones head
y no detectó operaciones de esquema pendientes.

La revisión manual y automatizada debe confirmar:

- `GET /api/v1/profile` devuelve exclusivamente el perfil del bearer
  autenticado o 404 si todavía no existe;
- `PUT /api/v1/profile` crea o reemplaza el perfil completo y trata los
  campos opcionales omitidos o nulos como valores eliminados;
- el cliente no puede enviar `id`, `user_id`, `created_at` ni `updated_at`;
- la altura se almacena en centímetros y la presentación imperial solo se
  convierte en el frontend;
- la restricción uno a uno y el servicio resuelven de forma controlada las
  creaciones concurrentes;
- la eliminación del usuario borra su perfil en cascada;
- dos usuarios permanecen aislados;
- la sesión expirada se trata sin persistir ni exponer el access token;
- la revisión `20260730_0004` es reversible y no deja cambios de esquema
  pendientes;
- no aparecen secretos, tokens, payloads de perfil ni datos personales en
  logs, DOM o Git.

En el pull request #10 de 3B.1, `Frontend`, `Backend quality` y
`PostgreSQL integration` finalizaron correctamente. El job de PostgreSQL
incluyó la migración y la suite real de perfiles, y el pull request fue
fusionado en `main`; no queda validación remota pendiente para 3B.1.

## Verificación completa del bloque 3B.2A

3B.2A no añade migraciones. Ejecuta calidad completa y después la misma suite
PostgreSQL de regresión para confirmar que autenticación, sesiones y perfil
continúan funcionando:

```powershell
Set-Location frontend
npm.cmd ci
npm.cmd run lint
npm.cmd run typecheck
npm.cmd run test
npm.cmd run build

Set-Location ..\backend
uv sync --locked
uv lock --check
uv run ruff check .
uv run ruff format --check .
uv run mypy app tests
uv run pytest

# Con las variables de integración definidas en esta guía:
uv run alembic upgrade head
uv run alembic current --check-heads
uv run alembic check
uv run pytest integration_tests -m integration

Set-Location ..
git diff --check
git status --short --untracked-files=all
```

Comprueba además en PostgreSQL que las únicas tablas propias sigan siendo
`alembic_version`, `users`, `auth_sessions` y `user_profiles`; 3B.2A no debe
crear tablas de fuentes, importaciones, revisiones o valores corporales.

La validación local debe confirmar:

- fixture sintético sin identidad, comentarios, enlaces, fórmulas ni
  propiedades personales;
- lectura de secciones, fechas, valores numéricos y textos con coma decimal;
- rechazo de archivos grandes, formatos distintos de `.xlsx`, contenedores
  inseguros, protección, macros y fórmulas corporales;
- 200 para la previsualización válida y errores 401, 403, 413, 415 y 422;
- OpenAPI sin `user_id` y respuestas sin nombre de archivo, celdas arbitrarias,
  tokens ni rutas temporales;
- selector accesible, análisis, agrupación, avisos, bloqueos, desconocidos,
  errores, reintento y cambio de archivo;
- ausencia de Web Storage, IndexedDB, cookies y persistencia PostgreSQL para el
  archivo y sus mediciones;
- fingerprint estable ante estilos y distinto ante un cambio real.

La validación local de 3B.2A finalizó correctamente con 137 pruebas backend,
38 pruebas frontend y 12 pruebas de integración sobre PostgreSQL real. El
ciclo de Alembic bajó hasta `base`, volvió a `head`, no detectó operaciones
pendientes y la inspección confirmó exclusivamente `alembic_version`, `users`,
`auth_sessions` y `user_profiles`. Una petición HTTP real autenticada devolvió
200, adaptador V1, 83 valores reconocidos y ningún `user_id`. Uvicorn se detuvo
y la base de prueba dedicada se eliminó después de la comprobación.

En el pull request #12 de 3B.2A, `Frontend`, `Backend quality` y
`PostgreSQL integration` finalizaron correctamente. El adaptador V1 se
contrastó con una copia anonimizada que conserva la estructura técnica del
Excel real y el pull request fue fusionado en `main`; no queda validación
remota ni funcional pendiente para 3B.2A.

## Verificación completa del bloque 3B.2B

3B.2B añade la revisión Alembic `20260731_0005` y requiere PostgreSQL real.
Con la base dedicada `agente_fitness_test` y las variables de la sección de
integración, ejecuta:

```powershell
Set-Location frontend
npm.cmd ci
npm.cmd run lint
npm.cmd run typecheck
npm.cmd run test
npm.cmd run build

Set-Location ..\backend
uv sync --locked
uv lock --check
uv run ruff check .
uv run ruff format --check .
uv run mypy app tests
uv run pytest

uv run alembic upgrade head
uv run alembic current --check-heads
uv run alembic check
uv run alembic downgrade 20260730_0004
uv run alembic upgrade head
uv run pytest integration_tests -m integration

Set-Location ..
git diff --check
git status --short --untracked-files=all
```

La validación debe confirmar:

- cuatro tablas normalizadas, UUID, timestamps UTC, `NUMERIC(14,6)`, claves
  compuestas por propietario y borrado de cuenta en cascada;
- una única versión vigente por identidad, cadena inmutable y migración
  reversible sin operaciones Alembic pendientes;
- identidad de revisión estable separada del hash de contenido;
- revisiones nuevas, idénticas, modificadas, bloqueadas y excluidas;
- reanálisis del archivo en plan y confirmación, fingerprints coherentes y
  rechazo de decisiones o valores no autorizados;
- replay 200 con la misma `Idempotency-Key` y digest, 409 al reutilizarla con
  otra petición y un solo efecto ante reintentos concurrentes;
- bloqueo por fuente: dos confirmaciones paralelas con el mismo historial no
  pueden ganar ambas;
- rollback total ante un fallo genérico después de iniciar la persistencia,
  sin importación, revisiones ni incremento de `history_version` residuales;
- versionado explícito, consulta de vigentes y detalle normalizado;
- reversión transaccional, restauración de predecesora, repetición sin efectos
  y 409 cuando existe una versión posterior dependiente;
- 404 para fuentes, importaciones y revisiones de otro usuario;
- archivo, nombre físico, claves en claro, tokens y valores corporales ausentes
  de logs, Web Storage y respuestas técnicas;
- regresión completa de autenticación, sesión, perfil y previsualización 3B.2A.

La validación local de 3B.2B finalizó correctamente con 150 pruebas backend,
45 pruebas frontend y 16 pruebas de integración sobre PostgreSQL real. Se
comprobaron migración, downgrade y nuevo upgrade, idempotencia concurrente,
conflicto concurrente por versión, rollback forzado, aislamiento, versionado,
reversión y borrado en cascada.
Docker CLI no estaba instalado en esta estación, pero PostgreSQL local estaba
disponible y la suite usó exclusivamente la base dedicada
`agente_fitness_test`. La validación remota de los tres jobs continúa pendiente
del pull request.
