# Privacidad

## Propósito

Definir los principios de privacidad del proyecto y los límites del tratamiento de datos personales y sensibles en el contexto de Agente Fitness.

## Categorías de datos

- cuenta;
- perfil físico;
- objetivos;
- entrenamientos;
- medidas corporales;
- nutrición;
- conversaciones;
- recomendaciones;
- telemetría técnica.

## Finalidad

Los datos deben utilizarse para:

- permitir el seguimiento del usuario;
- ofrecer métricas deterministas y explicaciones guiadas;
- apoyar la gestión de rutinas y recomendaciones;
- mejorar la seguridad y trazabilidad del sistema.

## Minimización

El sistema debe recopilar y procesar solo los datos necesarios para la finalidad declarada. No debe enviarse al modelo más información de la necesaria ni almacenarse información innecesaria por defecto.

## Propiedad

El usuario conserva la titularidad de sus datos personales y de actividad. El sistema debe permitir el control del usuario sobre acceso, exportación y eliminación de datos, dentro de los límites técnicos y legales aplicables.

## Acceso

El acceso a datos privados debe estar limitado al usuario autenticado y a los componentes del sistema autorizados. No debe reutilizarse información privada de un usuario para otro.

## Separación entre usuarios

Los datos de un usuario deben tratarse de forma aislada respecto de los demás. Las consultas, recomendaciones y herramientas del agente deben operar dentro del contexto propietario del usuario autenticado.

## Autenticación y autorización

La autenticación se aplica en backend mediante un access token cuyo sujeto es
el UUID estable de la cuenta. Las rutas protegidas vuelven a resolver el
usuario en PostgreSQL y no aceptan un identificador arbitrario proporcionado
por el cliente. La autorización por propietario seguirá siendo obligatoria
cuando se incorporen recursos privados.

Las contraseñas solo se conservan como hashes Argon2id. Contraseñas, hashes,
secretos JWT y tokens completos no deben incluirse en respuestas ni logs. El
frontend conserva el access token solo en memoria; no utiliza almacenamiento
web persistente. El refresh token se entrega mediante cookie `HttpOnly` y
PostgreSQL conserva únicamente su digest SHA-256.

Cada renovación rota el refresh token y logout revoca la sesión activa. Las
operaciones basadas en cookie exigen un origen confiable, además de
`SameSite`, ruta limitada y CORS con credenciales para orígenes explícitos. Las
sesiones caducadas se eliminan oportunistamente y una sesión no sobrevive a la
eliminación futura de su cuenta.

El perfil básico recoge únicamente nombre visible, fecha de nacimiento y
altura opcionales, nivel de experiencia declarado, zona horaria y sistema de
unidades. No incorpora objetivos, historial corporal, lesiones, limitaciones,
equipamiento, nutrición ni campos libres. Su `user_id` se deriva del access
token, nunca se acepta desde el cliente y no se expone en la respuesta. La
eliminación de la cuenta elimina el perfil por cascada.

## Logs

Los logs técnicos deben evitar incluir datos sensibles o completos de prompts, herramientas y respuestas salvo justificación explícita. La trazabilidad debe equilibrarse con la minimización de datos. Las trazas técnicas deben utilizar resúmenes, identificadores y códigos de error cuando sea suficiente.

Los payloads completos del perfil, la fecha de nacimiento y la altura no deben
registrarse en logs ordinarios.

Las revisiones corporales futuras serán datos privados separados del perfil.
Bioimpedancia, pliegues, perímetros, valores bilaterales, archivos de origen y
resultados de importación no deberán aparecer en logs ordinarios. Una eventual
integración con Excel u OneDrive deberá aplicar minimización, autorización por
propietario y registro técnico sin valores corporales.

## Prompts y conversaciones

Los mensajes visibles pueden almacenarse según consentimiento, finalidad y política de retención. Los prompts del sistema y las instrucciones internas no se almacenan íntegramente por defecto. Los argumentos y resultados completos de herramientas no se registran por defecto. El razonamiento interno del modelo no se almacena.

## Herramientas del agente

Las herramientas del agente deben minimizar la cantidad de datos que manejan y no deben expedir secretos ni información innecesaria. Las ejecuciones de herramientas deben quedar registradas de forma resumida.

## Exportación y eliminación

El producto debe contemplar exportación y eliminación de datos. La experiencia de usuario debe resultar comprensible y observable, incluso si la implementación concreta aún no exista.

## Retención

La política final de retención debe dejarse como decisión pendiente. Deben distinguirse, al menos, los siguientes conceptos:

- eliminación visible para el usuario;
- borrado lógico;
- borrado físico;
- retención técnica;
- copias de seguridad.

## Copias de seguridad

Las copias de seguridad deben tratarse como una forma de retención técnica y deben gestionarse con políticas explícitas. No deben exponerse ni reutilizarse de forma innecesaria.

## Proveedores externos

Si se incorporan proveedores externos para autenticación, almacenamiento, IA o monitoreo, su tratamiento de datos debe documentarse y revisarse. No deben asumirse permisos amplios ni almacenamiento ilimitado.

## Secretos

No deben almacenarse secretos en Git, en texto plano en el repositorio ni en frontend. Las decisiones finales sobre gestión de secretos deben dejarse como propuestas pendientes.

## Datos de desarrollo y demostración

Los datos de desarrollo, demostración y pruebas deben separarse de los datos
reales para evitar mezclas y exposición accidental. Las pruebas de integración
de autenticación y perfil rechazan bases cuyo nombre no termine en `_test` o
`_ci` y eliminan exclusivamente las cuentas y datos asociados que crean.

## Incidentes

Debe existir un proceso conceptual de respuesta ante incidentes de privacidad o seguridad, aunque la política formal no sea aún definitiva.

## Decisiones pendientes

- Definir la política final de retención y borrado.
- Determinar el alcance exacto de logs y trazabilidad técnica.
- Formalizar el tratamiento de datos en proveedores externos.
- Establecer la política operativa de copias de seguridad y recuperación.
- Revisar la política final sobre conversaciones, consentimiento y retención con especialistas en privacidad y cumplimiento.
