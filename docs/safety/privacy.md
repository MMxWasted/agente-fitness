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

La autenticación y la autorización deben aplicarse en backend. La identidad del usuario debe obtenerse del contexto autenticado y no de un identificador arbitrario proporcionado por el cliente.

## Logs

Los logs técnicos deben evitar incluir datos sensibles o completos de prompts, herramientas y respuestas salvo justificación explícita. La trazabilidad debe equilibrarse con la minimización de datos. Las trazas técnicas deben utilizar resúmenes, identificadores y códigos de error cuando sea suficiente.

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

Los datos de desarrollo, demostración y pruebas deben separarse de los datos reales para evitar mezclas y exposición accidental.

## Incidentes

Debe existir un proceso conceptual de respuesta ante incidentes de privacidad o seguridad, aunque la política formal no sea aún definitiva.

## Decisiones pendientes

- Definir la política final de retención y borrado.
- Determinar el alcance exacto de logs y trazabilidad técnica.
- Formalizar el tratamiento de datos en proveedores externos.
- Establecer la política operativa de copias de seguridad y recuperación.
- Revisar la política final sobre conversaciones, consentimiento y retención con especialistas en privacidad y cumplimiento.
