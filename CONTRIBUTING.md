# Contribuir a Agente Fitness

## Estado actual del proyecto

Agente Fitness se encuentra en una fase de planificación y documentación previa a la implementación. Actualmente no existe una aplicación ejecutable ni una infraestructura técnica operativa completa.

## Requisitos generales para contribuir

- Leer primero [AGENTS.md](AGENTS.md), [README.md](README.md), [docs/PLAN_MAESTRO.md](docs/PLAN_MAESTRO.md) y los documentos relevantes del área que se vaya a tocar.
- Mantener el alcance de la tarea alineado con el objetivo declarado.
- Evitar introducir cambios ajenos a la tarea o a la documentación asociada.
- Documentar cambios de comportamiento, arquitectura, seguridad o alcance cuando sean relevantes.

## Obligación de revisar la guía del repositorio

Antes de trabajar en una tarea, es obligatorio revisar [AGENTS.md](AGENTS.md) y, cuando proceda, la documentación específica de producto, arquitectura, desarrollo o seguridad.

## Flujo recomendado de trabajo

1. Actualizar la rama principal local.
2. Crear una rama de trabajo con un nombre claro y específico.
3. Trabajar en una tarea acotada y verificable.
4. Ejecutar las verificaciones aplicables a la tarea.
5. Revisar el diff antes de finalizar.
6. Crear el commit si la tarea lo requiere y si el usuario ha solicitado explícitamente esa acción.
7. Abrir un pull request con resumen, criterios de aceptación y riesgos conocidos.

## Formato de commits

- Los commits deben ser claros, cortos y expresar el cambio realizado.
- Se recomienda seguir un estilo tipo Conventional Commits.
- Los mensajes deben estar en inglés.

## Pull requests

Cada pull request debe incluir:

- resumen del problema o necesidad;
- cambios realizados;
- criterios de aceptación;
- riesgos o límites conocidos;
- documentación afectada;
- verificaciones ejecutadas.

Para el flujo de trabajo detallado de ramas, commits, revisiones y resolución de conflictos, consultar [docs/development/git-workflow.md](docs/development/git-workflow.md). Para los criterios de finalización aplicables a la tarea, consultar [docs/development/definition-of-done.md](docs/development/definition-of-done.md).

## Criterios de aceptación

Toda tarea debe contar con criterios de aceptación verificables. Si una tarea no puede verificarse de forma observable, debe documentarse explícitamente.

## Actualización documental

Cuando una tarea modifique comportamiento, alcance, arquitectura, seguridad, API o procesos, debe actualizarse la documentación relevante. No se debe describir como implementado algo que aún no exista en el repositorio.

## Pruebas y verificaciones

- Las verificaciones deben ser proporcionales al alcance de la tarea.
- En tareas documentales, la verificación principal debe centrarse en la coherencia del contenido, los enlaces y la ausencia de errores de formato evidentes.
- Cuando exista un cambio técnico, deben ejecutarse las pruebas y verificaciones aplicables.

## Tratamiento de secretos

- No deben incluirse secretos ni credenciales en el repositorio.
- Los valores sensibles deben mantenerse fuera del control de versiones.

## Revisión de cambios

Antes de finalizar una tarea, es obligatorio revisar el diff para comprobar que:

- el cambio es coherente con el alcance;
- no se han introducido modificaciones ajenas;
- no hay cambios no deseados.

## Prohibiciones

- No modificar archivos fuera del alcance de la tarea.
- No introducir cambios de infraestructura o implementación sin solicitud explícita.
- No crear commits ni ramas automáticamente salvo instrucción expresa.
