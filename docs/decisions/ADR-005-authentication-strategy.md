# ADR-005 — Estrategia de autenticación

- Identificador: `ADR-005`
- Estado: `Accepted`

## Contexto

El backend necesita identificar al usuario antes de incorporar recursos
privados. El bloque 3A.1 solo requiere una identidad técnica y un access token
para clientes de la API; la interfaz web, la persistencia de sesión en el
navegador y el ciclo de renovación pertenecen a bloques posteriores.

## Fuerzas o criterios de decisión

- Protección de credenciales, secretos y tokens.
- Contrato estándar y documentable mediante FastAPI y OpenAPI.
- Identidad estable independiente del correo.
- Caducidad acotada y configuración tipada.
- Implementación mínima compatible con clientes web y móviles futuros.
- Separación entre autenticación, autorización por propietario y gestión de
  sesión avanzada.

## Decisión

La primera versión utiliza correo normalizado y contraseña para autenticar.
Las contraseñas se almacenan exclusivamente como hashes Argon2id generados por
la configuración recomendada de `pwdlib`.

El backend emite un access token JWT bearer firmado con HS256. El secreto se
carga desde entorno, se representa como valor secreto y debe tener al menos 32
bytes. El token contiene únicamente `sub`, `iat` y `exp`: `sub` es el UUID
estable del usuario y la duración predeterminada es 30 minutos, configurable
entre 5 minutos y 24 horas. La decodificación fija explícitamente HS256 y exige
los tres claims.

El token se presenta en `Authorization: Bearer <token>`. Cada petición
protegida resuelve de nuevo el usuario en PostgreSQL y rechaza identidades
inexistentes o inactivas. Nunca se acepta un `user_id` proporcionado libremente
por el cliente para establecer la identidad.

El alcance original de esta decisión no definía refresh tokens, revocación,
cierre de sesión servidor, cookies ni almacenamiento en navegador. Tampoco
define recuperación de cuenta, verificación de correo, MFA ni proveedores
externos.

La gestión de sesión web renovable del bloque 3A.2 se formaliza de forma
compatible en [ADR-013](ADR-013-session-management.md). ADR-005 continúa
definiendo la identidad, la contraseña y el access token bearer; ADR-013 añade
la sesión servidor, el refresh token y los controles del navegador.

## Alternativas consideradas

- **Sesión backend con cookie `HttpOnly`:** reduce la exposición del token a
  JavaScript, pero requiere decidir topología de dominios, protección CSRF y
  almacenamiento de sesiones.
- **Access token más refresh token:** mejora la continuidad de sesión, pero
  exige rotación, revocación y almacenamiento seguro que no son necesarios
  para la identidad mínima.
- **Proveedor externo de identidad:** aporta capacidades maduras, pero añade
  dependencia, coste y tratamiento de datos antes de que exista esa necesidad.
- **JWT bearer de corta duración sin renovación:** cubre el contrato actual con
  menos estado y es la opción adoptada para 3A.1.

## Consecuencias positivas

- FastAPI y OpenAPI exponen un flujo bearer estándar.
- La identidad viaja como UUID y no duplica datos personales en el token.
- La caducidad limita la ventana de uso de un token filtrado.
- Argon2id permite hashes con salt y coste administrados por una biblioteca
  mantenida.
- La resolución contra PostgreSQL impide usar tokens de usuarios eliminados o
  inactivos.

## Consecuencias negativas

- Un access token válido no puede revocarse individualmente antes de caducar.
- El alcance original de 3A.1 no proporcionaba continuidad automática de
  sesión ni definía el almacenamiento y la protección del token en el cliente
  web. ADR-013 resolvió ambos aspectos para 3A.2.
- HS256 requiere custodiar y rotar un secreto compartido en cada entorno.

## Riesgos

- Robo y reproducción de un token durante su vigencia.
- Almacenamiento inseguro en el navegador si se implementa sin una decisión
  posterior.
- Fuerza bruta sobre login mientras no exista rate limiting.
- Configurar en producción el marcador local o un secreto insuficiente.

## Impacto en seguridad y privacidad

Las respuestas y logs no incluyen contraseñas, hashes, secretos ni tokens
completos. Los errores de login no distinguen entre correo inexistente y
contraseña incorrecta. El registro puede indicar un correo duplicado porque el
conflicto es necesario para completar ese flujo. Los datos de pruebas deben
usar una base separada de los datos locales normales.

El uso del encabezado bearer no introduce por sí mismo cookies ni protección
CSRF. ADR-013 añadió una cookie de refresh `HttpOnly` y protección de origen
para las operaciones de sesión del cliente web. Rate limiting y monitoreo de
abuso quedan como endurecimiento futuro.

## Condiciones de revisión

La revisión previa a implementar persistencia de sesión, refresh tokens,
cookies y revocación se realizó mediante ADR-013. Revisar conjuntamente ambas
decisiones antes de incorporar clientes móviles, recuperación de cuenta,
proveedores externos o despliegue distribuido. Un cambio incompatible debe
registrarse mediante un nuevo ADR que sustituya este.

## Documentos relacionados

- [Diseño conceptual de la API](../architecture/api-design.md)
- [Modelo de datos](../architecture/data-model.md)
- [Privacidad](../safety/privacy.md)
- [ADR-012 — Estrategia de despliegue](ADR-012-deployment-strategy.md)
- [ADR-013 — Gestión de sesión web renovable](ADR-013-session-management.md)
