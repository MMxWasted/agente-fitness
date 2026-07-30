# ADR-013 — Gestión de sesión web renovable

- Identificador: `ADR-013`
- Estado: `Accepted`

## Contexto

ADR-005 define la identidad mediante correo y contraseña, junto con un access
token JWT bearer de corta duración. El bloque 3A.2 necesita mantener esa
compatibilidad y añadir continuidad de sesión para el frontend sin exponer una
credencial renovable a JavaScript ni convertir el access token en estado
persistente del navegador.

La topología de producción continúa pendiente en ADR-012. Por tanto, esta
decisión debe ser segura para el desarrollo con frontend y API en orígenes
locales distintos, y debe rechazar configuraciones de producción que relajen
los controles necesarios.

## Fuerzas o criterios de decisión

- Minimizar el impacto de XSS sobre credenciales de larga duración.
- Proteger las operaciones autenticadas mediante cookie frente a CSRF.
- Revocar la sesión activa de forma observable durante logout.
- Mantener el access token y `GET /api/v1/users/me` compatibles con ADR-005.
- Garantizar una única rotación válida ante solicitudes concurrentes.
- Evitar almacenar tokens en texto plano.
- Mantener una configuración reproducible y validada por entorno.
- No añadir dependencias cuando la biblioteca estándar sea suficiente.

## Decisión

### Access token

El access token continúa siendo un JWT bearer de corta duración con los claims
`sub`, `iat` y `exp` definidos en ADR-005. El frontend lo conserva solo en
memoria. No se escribe en `localStorage`, `sessionStorage`, IndexedDB ni en una
cookie accesible desde JavaScript.

Las rutas privadas continúan recibiéndolo mediante
`Authorization: Bearer <token>`. La cookie de refresh no sustituye la
autenticación bearer ni se consulta directamente desde `GET /users/me`.

### Refresh token y persistencia

Cada login correcto crea una sesión servidor y un refresh token opaco generado
con un generador criptográficamente seguro de la biblioteca estándar. El token
posee entropía suficiente para no depender de una contraseña elegida por una
persona.

El refresh token completo solo se entrega mediante una cookie `HttpOnly`. En
PostgreSQL se almacena exclusivamente su digest SHA-256 hexadecimal. SHA-256 es
adecuado aquí porque la entrada es una credencial aleatoria de alta entropía;
un hash de contraseña deliberadamente costoso no aporta una protección
equivalente y encarecería cada renovación.

La tabla `auth_sessions` relaciona la sesión con `users`, conserva creación,
actualización, expiración y revocación, y aplica unicidad al digest. La clave
foránea usa `ON DELETE CASCADE`: una credencial de sesión no tiene valor
histórico ni debe sobrevivir a la eliminación futura de la cuenta.

### Rotación, concurrencia y revocación

Cada renovación correcta genera un refresh token nuevo y reemplaza el digest
anterior dentro de la misma transacción que actualiza la sesión. La consulta
que identifica el digest vigente bloquea la fila para actualización. Después
de la primera confirmación, una solicitud concurrente con el digest anterior
ya no cumple la condición; como máximo una renovación puede completarse.

La rotación no amplía la expiración absoluta creada durante el login. La nueva
cookie conserva el tiempo restante de la sesión original, evitando que una
sesión utilizada continuamente se vuelva indefinida.

Un refresh token anterior, desconocido, caducado o revocado recibe el mismo
error genérico. Los usuarios inactivos no pueden renovar.

Logout marca la sesión como revocada cuando puede identificarla y siempre
elimina la cookie. Con una petición CSRF válida, repetir logout o enviarlo sin
cookie produce `204 No Content` y no revela si la sesión existía.

### Cookie

La cookie de refresh se configura explícitamente:

- nombre validado y sin prefijo reservado incompatible;
- `HttpOnly` siempre activo;
- `Secure` configurable, obligatorio en producción;
- `SameSite=Lax` por defecto; `Strict` también es válido;
- `SameSite=None` queda prohibido hasta resolver la topología y protección
  adicional correspondiente;
- dominio omitido por defecto para crear una cookie host-only;
- ruta limitada a `/api/v1/auth`;
- `Max-Age` y `Expires` alineados con la expiración de la sesión.

El nombre, dominio, ruta, duración, `Secure` y `SameSite` se cargan desde
configuración tipada. Los valores locales son públicos y no constituyen
secretos.

### Protección CSRF

`HttpOnly` protege frente a lectura por JavaScript, pero no evita que el
navegador adjunte la cookie a una solicitud maliciosa. Los endpoints que
consumen la cookie, `POST /auth/refresh` y `POST /auth/logout`, exigen un
encabezado `Origin` presente y perteneciente a una lista explícita de orígenes
de confianza.

`POST /auth/token` rechaza un `Origin` presente que no sea de confianza para
evitar login CSRF, pero conserva compatibilidad con clientes OAuth2 no
navegador que no envían `Origin`. Los endpoints de refresh y logout no admiten
esa excepción porque su credencial procede exclusivamente de una cookie del
navegador.

Los orígenes de confianza son URLs HTTP o HTTPS sin ruta, query, fragmento ni
comodines. Deben estar incluidos en los orígenes CORS permitidos. Este control
se combina con `SameSite`, una cookie host-only y métodos POST; ninguno se
considera suficiente de forma aislada.

### CORS

CORS permite credenciales porque el frontend necesita recibir y enviar la
cookie `HttpOnly`. Los orígenes siguen siendo explícitos y nunca se admite `*`
junto con credenciales. Los métodos y encabezados permitidos permanecen
restringidos a los utilizados por la aplicación.

### Limpieza

Las sesiones caducadas se eliminan de forma oportunista al crear o renovar
sesiones, mediante una consulta apoyada por un índice de expiración. Las
sesiones revocadas se conservan hasta su expiración para mantener el estado de
revocación durante su vida útil original.

Esta estrategia evita incorporar un scheduler antes de necesitarlo. Se deberá
añadir un proceso periódico y acotado si el volumen, la observabilidad o el
despliegue demuestran que la limpieza oportunista no es suficiente.

## Contratos resultantes

- `POST /api/v1/auth/token`: autentica, crea la sesión, establece la cookie y
  devuelve el access token bearer.
- `POST /api/v1/auth/refresh`: exige cookie y origen confiable, rota la sesión,
  establece una cookie nueva y devuelve un access token nuevo.
- `POST /api/v1/auth/logout`: exige origen confiable, revoca cuando procede,
  elimina la cookie y devuelve 204 de forma idempotente.
- `GET /api/v1/users/me`: continúa dependiendo solo del access token bearer.

El refresh token nunca aparece en JSON, URL, documentación de ejemplo, logs o
mensajes de error.

## Alternativas consideradas

- **Access y refresh en almacenamiento web:** simplifica el cliente, pero una
  XSS puede extraer ambas credenciales; se rechaza.
- **Refresh JWT sin estado servidor:** reduce persistencia, pero no ofrece
  revocación inmediata ni rotación concurrente fiable; se rechaza.
- **Sesión completamente opaca en cookie:** reduce JWT en el cliente, pero
  rompe el contrato bearer existente y limita clientes API; se rechaza en este
  bloque.
- **Cookie de refresh más token CSRF de doble envío:** es válida, pero añade
  otro valor y sincronización cliente. La validación estricta de `Origin`,
  combinada con SameSite y orígenes explícitos, cubre la topología adoptada.
- **Refresh opaco con digest servidor:** permite rotación, revocación y
  almacenamiento mínimo sin nuevas dependencias; es la alternativa adoptada.

## Consecuencias positivas

- El navegador no puede leer la credencial renovable.
- Una fuga de la base no expone refresh tokens utilizables directamente.
- Logout revoca la sesión activa antes de su caducidad.
- Las carreras de renovación tienen un único ganador.
- El access token sigue siendo compatible con FastAPI, OpenAPI y clientes API.
- La implementación usa primitivas estándar y la persistencia existente.

## Consecuencias negativas

- CORS y cookies pasan a depender de una configuración coherente por entorno.
- El backend mantiene estado de sesión y requiere una migración.
- El access token ya emitido sigue siendo válido hasta expirar después de
  logout; la revocación inmediata aplica a la renovación.
- Los clientes no navegador que quieran renovar deberán reproducir el contrato
  de cookie y enviar un origen confiable.
- La limpieza oportunista no sustituye indefinidamente una tarea operativa en
  instalaciones de alto volumen.

## Riesgos

- XSS puede usar temporalmente el access token que existe en memoria.
- Una lista de orígenes demasiado amplia debilita la protección CSRF.
- Una configuración incorrecta de `Secure`, dominio o `SameSite` puede impedir
  el flujo o ampliar el alcance de la cookie.
- La reproducción de un refresh token robado antes de su primera rotación
  sigue siendo posible.
- Sin rate limiting, login continúa expuesto a intentos de fuerza bruta.
- Relojes desalineados pueden afectar expiración y atributos de cookie.

## Impacto en seguridad y privacidad

La sesión almacena solo identificadores, digest y timestamps técnicos. No
duplica correo, contraseña ni datos fitness. Tokens, cookies, digests y
secretos se excluyen de respuestas públicas, representaciones de modelos y
logs.

Las pruebas deben comprobar atributos de cookie, CORS, CSRF, errores genéricos,
rotación, revocación, concurrencia e inactividad. Los datos de integración
siguen aislados en bases cuyo nombre termina en `_test` o `_ci`.

## Condiciones de revisión

Revisar esta decisión si se adopta una topología cross-site, clientes móviles,
gestión visual de dispositivos, cierre de todas las sesiones, detección de
reutilización por familias, rotación de secretos distribuida, una política
formal de retención o un scheduler operativo.

`SameSite=None`, un dominio compartido amplio o una relajación del control de
origen requieren una revisión explícita. La estrategia también deberá
coordinarse con ADR-012 antes del despliegue.

## Documentos relacionados

- [ADR-005 — Estrategia de autenticación](ADR-005-authentication-strategy.md)
- [ADR-002 — PostgreSQL](ADR-002-postgresql.md)
- [ADR-012 — Estrategia de despliegue](ADR-012-deployment-strategy.md)
- [Diseño de la API](../architecture/api-design.md)
- [Modelo de datos](../architecture/data-model.md)
- [Privacidad](../safety/privacy.md)
