# Diseño conceptual de la API

## Objetivos

Definir un diseño conceptual de API que sea coherente con la arquitectura prevista, priorice la seguridad y la privacidad, y preserve una separación clara entre frontend, backend y servicios de dominio.

## Principios

- La API debe ser una capa de acceso controlada para el frontend y el agente.
- La autenticación y la autorización deben aplicarse en backend.
- Los endpoints deben mantener la lógica de negocio mínima.
- Los contratos deben ser explícitos y documentables.
- Las respuestas deben evitar exponer datos sensibles ni stack traces.
- Los cambios de contrato deben tratarse como decisiones que requieren revisión.

## Grupos conceptuales de recursos

- auth
- users/profile
- goals
- exercises
- routines
- workouts
- measurements
- nutrition
- analytics
- agent
- privacy/export
- account deletion

## Autenticación

El bloque 3A.1 implementa correo y contraseña con access tokens JWT bearer,
según [ADR-005](../decisions/ADR-005-authentication-strategy.md). El access
token contiene `sub` con el UUID del usuario, `iat` y `exp`; la duración es
configurable y vale 30 minutos por defecto. Firma, caducidad y claims se
validan antes de resolver el usuario actual en PostgreSQL.

El campo técnico `username` del formulario OAuth2 contiene el correo
electrónico. La identidad siempre procede del token validado y nunca de un
identificador arbitrario proporcionado por el cliente.

### Contratos implementados

| Método y ruta | Entrada | Respuesta correcta | Errores relevantes |
| --- | --- | --- | --- |
| `POST /api/v1/auth/register` | JSON con `email` y `password` | 201 y usuario público | 409 correo registrado; 422 entrada inválida |
| `POST /api/v1/auth/token` | `application/x-www-form-urlencoded` con `username` y `password` | 200 con `access_token` y `token_type: bearer` | 401 credenciales incorrectas |
| `GET /api/v1/users/me` | `Authorization: Bearer <token>` | 200 y usuario público | 401 token o identidad inválidos; 403 cuenta inactiva |

El usuario público contiene `id`, `email`, `is_active`, `created_at` y
`updated_at`. Ningún contrato expone la contraseña ni `password_hash`. El
registro no emite token implícitamente. Los errores de login son genéricos para
no distinguir correo inexistente de contraseña incorrecta.

Refresh tokens, revocación, cierre de sesión servidor, cookies, recuperación,
verificación de correo, MFA y login social no están implementados. Tampoco
existe aún almacenamiento de token ni interfaz de autenticación en frontend.

## Autorización

Cada recurso privado debe estar vinculado al usuario autenticado. El backend debe comprobar que el usuario solo puede operar sobre sus propios datos. Los recursos compartidos o públicos se manejarán de forma aislada y documentada. Los recursos privados no deben usar un user_id libremente proporcionado en la ruta o el cuerpo para decidir el propietario; la propiedad procede del contexto autenticado.

## Validación

- Validación de entrada en backend.
- Rechazo de datos incompletos o incoherentes.
- Validación de permisos y reglas de negocio.
- Distinción entre error de validación, conflicto de negocio y error técnico.

## Formatos de entrada y salida

Se prevé un formato JSON para requests y responses. Los recursos deben exponer un esquema consistente y se debe evitar incluir información interna o sensible en las respuestas públicas.

## Errores

Los errores conceptuales deben estructurarse con:

- code
- message
- details
- request_id

No se deben incluir stack traces ni datos sensibles en las respuestas.

## Paginación

Los listados grandes deben soportar paginación por cursor o página, según la decisión formal. Debería existir un límite de tamaño de respuesta y un orden definido.

## Filtros y ordenación

- Filtros por fecha, estado, tipo de recurso o propietario autenticado.
- Ordenación consistente por fecha, relevancia o nombre según el recurso.
- Los filtros deben aplicarse en backend y no confiarse en el cliente.

## Operaciones idempotentes

Las operaciones sensibles, como la creación o la confirmación de acciones, deben diseñarse para evitar efectos duplicados. La API debe documentar si una operación puede repetirse de forma segura. La estrategia concreta de idempotencia para operaciones sensibles o repetibles queda pendiente.

## Concurrencia

Se prevé que operaciones como la activación de rutina, la confirmación de una propuesta o la actualización de un recurso sensible deban manejarse con reglas explícitas para evitar conflictos de negocio. La estrategia concreta deberá decidirse entre control optimista, versiones de recurso u otra estrategia equivalente.

## Versionado

Se prevé una versión explícita de la API, por ejemplo /api/v1/. El versionado debe facilitar cambios progresivos sin romper el cliente de forma inesperada.

## Documentación OpenAPI

La API debe documentarse de forma formal mediante OpenAPI. El objetivo es que la interfaz tenga un contrato claro para el frontend y para el agente, sin que la implementación se confunda con el diseño.

## Límites y rate limiting

Se prevé un límite de uso para evitar abuso, especialmente en endpoints de agente, autenticación, exportación y operaciones sensibles. Los límites deben ser documentados como pending hasta que exista una decisión formal.

## Trazabilidad

Cada request debe poder asociarse a un identificador único de trazabilidad. Este identificador debe ser útil para debugging y para auditoría, pero sin exponer información sensible.

## Privacidad

La API debe evitar filtrar información innecesaria y debe respetar las reglas de minimización. No debe exponer datos privados de otros usuarios ni registrar información sensible en logs técnicos de forma indiscriminada.

## Códigos de error conceptuales

- 401: no autenticado.
- 403: autenticado pero sin autorización.
- 404: recurso inexistente o no visible.
- La política de ocultar o revelar la existencia de recursos ajenos debe decidirse antes de implementar la autorización.

## Ejemplos conceptuales de rutas

- GET /api/v1/profile
- GET /api/v1/goals/active
- POST /api/v1/routines
- GET /api/v1/routines/{routine_id}
- POST /api/v1/workouts
- GET /api/v1/workouts/{workout_id}
- GET /api/v1/analytics/weekly-summary
- POST /api/v1/agent/conversations
- GET /api/v1/privacy/export
- POST /api/v1/account/deletion

Estas rutas son conceptuales y no representan una implementación existente.

## Estructura conceptual de errores

```json
{
  "code": "validation_error",
  "message": "Los datos proporcionados no son válidos.",
  "details": ["El campo email es obligatorio."],
  "request_id": "req-123"
}
```

## Diferenciación de errores

- Validación: datos incompletos o inválidos.
- Conflicto de negocio: regla de negocio violada, por ejemplo una rutina activa ya existente.
- No autenticado: la sesión o token no es válida.
- No autorizado: el usuario intenta acceder a un recurso no permitido.
- Recurso inexistente: el recurso solicitado no existe o no es visible para el usuario autenticado.
- Límite de uso: se ha excedido el límite de uso o rate limit.
- Error interno: fallo inesperado del sistema.

## Decisiones pendientes

- Definir renovación, revocación, almacenamiento del cliente y gestión
  avanzada de sesión sobre la base acotada de ADR-005.
- Determinar si los recursos serán paginados por cursor o por offset.
- Formalizar los límites de rate limiting y los requisitos de trazabilidad.
- Decidir el formato definitivo de errores y de respuestas comunes.
