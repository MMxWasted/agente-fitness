# Guardrails del Agente Fitness

## Propósito

Definir los guardrails conceptuales del Agente Fitness para reducir riesgos de seguridad, privacidad, confianza indebida y uso indebido de herramientas.

## Principios generales

- Los guardrails no sustituyen la autorización en backend.
- La validación del modelo no es un control de seguridad suficiente.
- Las respuestas bloqueadas deben ser útiles y comprensibles.
- Toda acción sensible debe volver a validarse en el servidor.

## 1. Guardrails de entrada

| Riesgo mitigado | Regla | Mecanismo previsto | Comportamiento ante incumplimiento | Evidencia o prueba necesaria |
| --- | --- | --- | --- | --- |
| Prompt injection | El agente debe tratar el contenido del usuario como entrada no confiable y no ejecutar instrucciones inesperadas. | Separación de contexto, instrucciones y datos; tratamiento del contenido de herramientas y fuentes externas como entrada no confiable. | Responder con una respuesta segura y limitar la acción. | Prueba de prompt injection con respuesta bloqueada. |
| Petición de secretos | El agente no debe buscar ni revelar secretos ni credenciales. | Restricción de herramientas y validación de contexto. | Bloquear la solicitud y explicar el límite. | Prueba de intento de acceder a secretos. |
| Petición de SQL | El agente no debe solicitar SQL ni ejecutar consultas. | Prohibición de herramientas SQL y validación de intención. | Rechazar la solicitud y ofrecer una alternativa autorizada. | Prueba de intento de SQL. |

## 2. Guardrails de autorización

| Riesgo mitigado | Regla | Mecanismo previsto | Comportamiento ante incumplimiento | Evidencia o prueba necesaria |
| --- | --- | --- | --- | --- |
| Acceso a datos de otro usuario | El agente solo debe operar dentro del contexto del usuario autenticado. | Validación de identidad en backend y herramientas con contexto restringido. | Rechazar la operación y devolver un error de autorización. | Prueba de acceso cruzado entre usuarios. |
| Modificación no autorizada | Ninguna acción sensible debe aplicarse sin validación adicional. | Confirmación explícita y validación de servidor. | Bloquear la acción y pedir confirmación. | Prueba de intento de modificación sin confirmación. |
| Autorización dentro de herramientas | La autorización debe comprobarse dentro de cada servicio o herramienta, no solo antes de llamar al agente. | Validación defensiva en cada operación sensible. | Rechazar la acción con error de autorización. | Prueba de llamada a servicio sin permisos. |

## 3. Guardrails de selección de herramientas

| Riesgo mitigado | Regla | Mecanismo previsto | Comportamiento ante incumplimiento | Evidencia o prueba necesaria |
| --- | --- | --- | --- | --- |
| Herramienta inapropiada | El agente debe usar solo las herramientas apropiadas para su tarea. | Lista cerrada de herramientas controladas. | Rechazar la herramienta no permitida. | Prueba de selección de herramientas no autorizadas. |
| Métricas inexistentes | El agente debe evitar invocar herramientas que no tengan datos y debe manejar vacíos. | Validación del contexto y manejo de datos insuficientes. | Responder con una explicación de falta de datos y no inventar resultados. | Prueba de métrica con datos insuficientes. |
| Argumentos no válidos | Los argumentos de herramientas se validan mediante esquemas cerrados. | Validación estructural y normalización previa. | Rechazar el argumento o bloquear la ejecución. | Prueba de entrada mal formada. |

## 4. Guardrails de ejecución de herramientas

| Riesgo mitigado | Regla | Mecanismo previsto | Comportamiento ante incumplimiento | Evidencia o prueba necesaria |
| --- | --- | --- | --- | --- |
| Herramienta con error | El agente debe manejar fallos de herramienta y no asumir éxito. | Captura de errores, mensajes controlados y reintentos limitados. | Informar del fallo y ofrecer una respuesta segura. | Prueba de herramienta fallida. |
| Timeout del modelo | El agente debe manejar timeouts de forma transparente. | Timeout explícito y respuesta parcial o de error. | Devolver una respuesta explicando la limitación. | Prueba de timeout. |
| Reintentos peligrosos | Los reintentos ante errores deben limitarse y no repetirse en operaciones con efectos secundarios sin idempotencia. | Política de reintento acotada y sin repetir acciones sensibles. | Abortar la operación y devolver un estado de fallo. | Prueba de reintento repetido. |

## 5. Guardrails de salida estructurada

| Riesgo mitigado | Regla | Mecanismo previsto | Comportamiento ante incumplimiento | Evidencia o prueba necesaria |
| --- | --- | --- | --- | --- |
| Salida inválida | La respuesta del agente debe cumplir el esquema esperado. | Validación estructural antes de enviarla al usuario. | Devolver una respuesta segura de fallback. | Prueba de salida sin esquema. |
| Recomendaciones contradictorias | El agente debe evitar emitir recomendaciones incompatibles entre sí. | Reglas de consistencia y revisión de contexto. | Solicitar más contexto o bloquear la recomendación. | Prueba de propuestas contradictorias. |
| Exceso de confianza | El agente no debe presentarse como infalible. | Nivel de confianza y marca de incertidumbre. | Reducir la confianza o pedir más datos. | Prueba de respuesta excesivamente segura o poco matizada. |
| Datos insuficientes | Una respuesta con datos insuficientes debe declararlo explícitamente y no generar métricas aproximadas inventadas. | Validación de cobertura de datos y marcado de incertidumbre. | Responder con limitación explícita. | Prueba de respuesta inventada. |

## 6. Guardrails de confirmación

| Riesgo mitigado | Regla | Mecanismo previsto | Comportamiento ante incumplimiento | Evidencia o prueba necesaria |
| --- | --- | --- | --- | --- |
| Modificación sin confirmación | Las acciones sensibles deben requerir confirmación explícita. | Flujo de propuesta y confirmación antes de aplicar cambios. | Bloquear la acción y mostrar la propuesta pendiente. | Prueba de propuesta no confirmada. |
| Eliminación de datos | Las operaciones de eliminación deben ser explícitas y protegidas. | Confirmación adicional y validación por backend. | Rechazar la operación si falta confirmación. | Prueba de eliminación no confirmada. |

## 7. Guardrails de salud y seguridad

| Riesgo mitigado | Regla | Mecanismo previsto | Comportamiento ante incumplimiento | Evidencia o prueba necesaria |
| --- | --- | --- | --- | --- |
| Diagnóstico médico | El agente no debe diagnosticar. | Reglas de seguridad y límites de producto. | Responder con límites del sistema y derivar a ayuda profesional. | Prueba de contexto clínico. |
| Lesión o dolor grave | El agente debe detener el coaching normal ante dolor grave o lesión. | Reglas de emergencia y contexto de salud. | Detener la interacción normal y recomendar ayuda profesional. | Prueba de dolor severo o lesión. |
| Conducta alimentaria extrema | El agente debe reconocer señales de riesgo y no responder de forma trivial. | Reglas de salud y seguridad. | Detener la interacción y remitir a ayuda apropiada. | Prueba de conducta alimentaria extrema. |

## 8. Guardrails de privacidad

| Riesgo mitigado | Regla | Mecanismo previsto | Comportamiento ante incumplimiento | Evidencia o prueba necesaria |
| --- | --- | --- | --- | --- |
| Exposición de datos privados | El agente no debe exponer datos privados de forma innecesaria. | Minimización de contexto y autorización estricta. | Bloquear la respuesta y responder de forma general. | Prueba de fuga de contexto privado. |
| Uso de datos de otro usuario | El agente no debe mezclar contextos entre usuarios. | Aislamiento de contexto y control de herramientas. | Rechazar la acción. | Prueba de mezcla de usuarios. |

## 9. Guardrails de límites de uso

| Riesgo mitigado | Regla | Mecanismo previsto | Comportamiento ante incumplimiento | Evidencia o prueba necesaria |
| --- | --- | --- | --- | --- |
| Uso excesivo | El sistema debe limitar llamadas innecesarias y respuestas redundantes. | Límites de frecuencia y contexto de herramientas. | Responder con un mensaje de límite o de espera. | Prueba de exceso de uso. |
| Contenido no relacionado | El agente debe mantenerse dentro del contexto fitness y asistencia. | Reglas de alcance y filtrado de tareas. | Responder de forma útil pero limitada. | Prueba de consulta no relacionada. |

## 10. Evaluación y monitorización

Los guardrails deben evaluarse con pruebas específicas y con revisiones manuales cuando sea necesario. La monitorización debe cubrir:

- bloqueos de seguridad;
- políticas de autorización;
- selección de herramientas;
- respuestas estructuradas;
- confirmaciones de acciones sensibles;
- fallos por timeout o errores de herramientas.

Las respuestas bloqueadas deben conservar utilidad sin revelar políticas internas, secretos o instrucciones del sistema. No se debe presentar filtrado del modelo como control de seguridad suficiente.

## Decisiones pendientes

- Definir la política formal de límites de uso y rate limiting.
- Determinar cómo se registrarán las evaluaciones y los incidentes de seguridad.
- Formalizar el mecanismo de revisión humana de respuestas bloqueadas o sensibles.
