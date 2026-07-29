# Definición de done

## 1. Criterios comunes

Una tarea solo puede considerarse completa cuando:

- se han cumplido los criterios de aceptación definidos;
- el alcance se ha respetado y no se han introducido cambios fuera de lo solicitado;
- se han aplicado las validaciones pertinentes al tipo de tarea;
- se han ejecutado las pruebas o verificaciones aplicables;
- se han considerado seguridad y privacidad cuando el cambio lo requiera;
- la documentación relevante ha sido actualizada cuando era necesario;
- se ha revisado el diff y no hay cambios inesperados;
- se han ejecutado las verificaciones pertinentes y se ha registrado el resultado;
- no se han incluido secretos ni credenciales;
- los riesgos pendientes se han comunicado de forma explícita.

## 2. Tarea documental

Una tarea documental se considera completa cuando:

- el contenido es coherente con el plan maestro y con los principios del producto;
- los documentos están enlazados de forma consistente;
- la terminología coincide con el glosario y las convenciones;
- no se presentan contradicciones evidentes con la visión del producto;
- el alcance y los límites quedan claros para quien lea la documentación.

## 3. Backend

Para cambios de backend, el done exige que:

- el comportamiento esperado quede documentado y verificable;
- los cambios de dominio, contratos o lógica estén alineados con la arquitectura prevista;
- la seguridad y la autorización se hayan considerado cuando el cambio lo requiera;
- las validaciones y los errores relevantes se hayan documentado o probado.

## 4. Frontend

Para cambios de frontend, el done exige que:

- el flujo principal sea comprensible y observable;
- los estados de carga, vacío y error queden contemplados cuando correspondan;
- el diseño siga siendo coherente con la prioridad mobile-first;
- los cambios de experiencia de usuario se documenten cuando afecten al producto.

## 5. Cambio de base de datos

Cuando una tarea modifique la base de datos, debe cumplirse que:

- el cambio se haya planificado de forma explícita;
- el impacto sobre el modelo de datos quede documentado;
- las migraciones o cambios de esquema se hayan tratado como parte del alcance;
- la compatibilidad y la reversibilidad se hayan considerado cuando sea aplicable.

## 6. Analítica determinista

Para una tarea relacionada con analítica determinista, el done exige que:

- la definición de la métrica esté documentada;
- las entradas y salidas sean conocidas y verificables;
- se contemplen casos límite y datos faltantes;
- existan pruebas con resultados esperados;
- no se deleguen cálculos importantes en el modelo de lenguaje.

## 7. Agente Fitness

Para tareas relacionadas con el Agente Fitness, el done exige que:

- las herramientas del agente sigan siendo limitadas y autorizadas;
- las respuestas estén basadas en datos y evidencias disponibles;
- las salidas relevantes estén validadas;
- no se inventen métricas ni registros;
- las acciones sensibles requieran confirmación explícita;
- las pruebas no dependan de llamadas reales obligatorias al modelo;
- se evalúen los riesgos de seguridad y privacidad cuando sea aplicable.

## 8. Fase del roadmap

Una fase del roadmap solo puede marcarse como finalizada cuando:

- todos sus entregables principales han sido revisados;
- sus criterios de aceptación han sido verificados;
- la documentación asociada está completa y coherente;
- no quedan pendientes críticos que comprometan la fase siguiente.
