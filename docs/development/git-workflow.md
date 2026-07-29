# Workflow de Git y colaboración

## Propósito

Este documento define un flujo de trabajo claro para colaborar con Agente Fitness sin introducir cambios no deseados ni perder trazabilidad.

## Propósito de main

La rama main debe mantenerse como referencia estable del proyecto. No debe utilizarse para trabajo experimental ni para cambios no revisados. Los cambios que entren en main deben estar documentados, revisados y alineados con el alcance vigente.

## Actualización segura de main

Antes de trabajar sobre una tarea, conviene revisar el estado de main y comprobar si hay cambios locales preexistentes. Cuando exista trabajo local no relacionado con la tarea, debe evitarse sobrescribirlo y debe documentarse el conflicto potencial.

## Creación de ramas

Las ramas deben crearse solo cuando la tarea lo requiera y deben reflejar el tipo de cambio. Los nombres de rama deben ser cortos, descriptivos y usar kebab-case.

Ejemplos:

- docs/add-product-scope
- feature/workout-logging
- fix/routine-authorization

## Formato de ramas

Se recomienda usar prefijos claros:

- docs/ para cambios documentales;
- feature/ para nuevas capacidades;
- fix/ para correcciones;
- refactor/ para cambios de estructura;
- test/ para pruebas;
- chore/ para tareas de mantenimiento.

## Conventional Commits

Se recomienda escribir los mensajes de commit en inglés y seguir un formato breve, por ejemplo:

- feat: add workout logging flow
- docs: add product scope documentation
- fix: correct routine authorization rules
- refactor: simplify roadmap structure

## Commits pequeños y enfocados

Los commits deben ser pequeños, dirigidos a una intención concreta y fáciles de revisar. Un cambio grande debe dividirse si es posible para reducir el riesgo de introducir errores o mezclar objetivos distintos.

## Pull requests

Cada pull request debe incluir:

- resumen del cambio;
- alcance y límites;
- criterios de aceptación;
- pruebas o verificaciones realizadas;
- riesgos o puntos pendientes;
- documentos relacionados actualizados.

## Revisión

Toda propuesta de cambio debe revisarse antes de integrarse. La revisión debe comprobar que el cambio respeta el alcance, la documentación y los principios del producto.

## Resolución de conflictos

En caso de conflicto, debe identificarse claramente qué cambios pertenecen a la tarea y qué cambios son preexistentes. No debe resolverse de forma automática ni sobrescribirse el trabajo ajeno sin confirmarlo.

## Prohibición de force push

No debe utilizarse force push salvo que exista una decisión expresa del equipo o del usuario para reescribir historia de forma controlada.

## Tratamiento de cambios locales preexistentes

Si existen cambios locales no relacionados con la tarea, deben revisarse antes de editar y debe evitarse mezclarlos con el trabajo actual. La tarea debe mantenerse enfocada.

## Cuándo actualizar CHANGELOG.md

El changelog debe actualizarse cuando un cambio afecte de forma observable al producto, a la documentación relevante o a la capacidad de seguimiento del proyecto. En tareas puramente internas o triviales, la actualización puede omitirse si no aporta valor.

## Cuándo crear etiquetas de versión

Las etiquetas de versión deben crearse solo cuando exista un hito de release o una revisión estable que el equipo quiera identificar explícitamente. No deben usarse para cambios menores de documentación o trabajo en progreso.

## Diferencia entre colaborador y Codex

- El colaborador humano es quien toma decisiones de producto, valida el alcance y aprueba cambios.
- Codex debe ayudar a ejecutar, revisar y documentar tareas, pero no debe crear ramas ni commits sin instrucción explícita.
- Codex debe trabajar dentro del alcance informado y debe evitar introducir cambios no solicitados.
