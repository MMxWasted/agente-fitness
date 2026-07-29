# Workflow de Codex para Agente Fitness

Este documento define cómo se utilizará Codex durante el desarrollo del proyecto. La idea es separar claramente el papel de Codex, que es el agente de desarrollo del repositorio, del papel del Agente Fitness, que será una funcionalidad del producto.

## 1. Diferencia entre Codex y el Agente Fitness

- Codex es el agente encargado de ayudar a construir, mantener y documentar el repositorio.
- El Agente Fitness es una funcionalidad del producto orientada a asesorar al usuario con datos del sistema.
- Codex no debe confundir su rol con el del asistente final del usuario.

## 2. Cuándo utilizar modo Plan

- El modo Plan se utilizará cuando Codex deba analizar, resumir o proponer sin modificar archivos.
- En estas tareas, Codex debe limitarse a leer, revisar y ofrecer recomendaciones, sin implementar ni alterar funcionalidad.

## 3. Cuándo permitir edición del workspace

- La edición del workspace se utilizará cuando Codex deba crear o modificar documentación, código o configuración.
- Una tarea documental puede requerir edición del workspace.
- Antes de editar, Codex debe revisar la documentación relevante, el estado de Git y los criterios de aceptación.

## 4. Revisión del estado de Git antes de cada tarea

- Antes de iniciar una tarea no trivial, Codex debe inspeccionar la rama actual y revisar el estado de Git.
- Debe identificar cambios existentes, ramas activas y posibles conflictos antes de editar archivos.
- Codex debe proponer una rama adecuada cuando sea necesario, pero no crear ni cambiar ramas salvo instrucción explícita.
- No debe sobrescribir cambios ajenos ni crear modificaciones no solicitadas.

## 5. Creación de ramas y commits

- Cuando una tarea requiera cambios en el repositorio, Codex debe proponer una rama con un nombre claro y específico.
- La rama debe reflejar el tipo de trabajo: feature, fix, docs, refactor, test o chore.
- Codex no debe crear commits salvo instrucción explícita.

## 6. Plantilla de prompt reutilizable

```text
Contexto:
- Descripción breve del problema o necesidad.
- Estado actual del repositorio y documentación relevante.

Objetivo:
- Qué debe conseguirse con esta tarea.

Criterios de aceptación:
- Qué debe verificarse para dar la tarea por cumplida.

Fuera de alcance:
- Qué no debe incluirse.

Archivos relevantes:
- Documentos o rutas que deben consultarse.

Restricciones:
- No implementar funciones no solicitadas.
- No crear dependencias nuevas sin justificación.
- No modificar archivos fuera del alcance.

Verificaciones:
- Qué comprobaciones deben ejecutarse.
- Qué evidencia debe dejarse en la respuesta final.

Formato de respuesta final:
- Resumen breve.
- Archivos modificados.
- Verificaciones ejecutadas.
- Riesgos o limitaciones.
```

## 7. Definición de criterios de aceptación

- Cada tarea debe tener criterios claros, medibles y verificables.
- Los criterios deben incluir, cuando sea pertinente, documentación, pruebas, revisión de impacto y coherencia con el plan maestro.
- No se debe considerar finalizada una tarea si no se han verificado los criterios relevantes.

## 8. Revisión del diff

- Antes de finalizar, Codex debe revisar el diff para comprobar que los cambios son coherentes, limitados y acordes con la solicitud.
- Debe evitar difusiones de cambios o modificaciones no pedidas.

## 9. Ejecución de pruebas

- Si una tarea incluye cambios que puedan afectar comportamiento o calidad, debe ejecutarse la verificación correspondiente.
- En esta fase documental, las pruebas no implican código ejecutable; la validación principal será la coherencia del contenido y la ausencia de errores de formato evidentes.

## 10. Actualización documental

- Siempre que un cambio afecte producto, arquitectura, seguridad, API o procesos, debe actualizarse la documentación pertinente.
- No se debe describir como implementado algo que aún no esté presente en el repositorio.

## 11. Cuándo realizar commits

- No se deben crear commits salvo que el usuario lo solicite explícitamente.
- Los cambios en el workspace deben revisarse antes de confirmarlos mediante commit.
- En tareas de documentación previa, los cambios del workspace deben revisarse antes de crear un commit, y Codex no debe confirmar esos cambios automáticamente.

## 12. Cómo actuar ante fallos

- Si una tarea no puede completarse por falta de contexto, bloqueo técnico o contradicción documental, Codex debe señalarlo de forma precisa.
- No debe inventar soluciones ni asumir decisiones no aprobadas.
- Debe indicar claramente qué falta para continuar.

## 13. Cómo evitar implementar tareas no solicitadas

- Codex debe respetar los límites del prompt y del alcance informado.
- Si una solicitud podría derivar en una implementación completa, debe detenerse y aclarar la frontera entre documentación y ejecución.
- No debe generar frontend, backend, dependencias, infraestructura ni código de aplicación salvo que se lo soliciten explícitamente.

## 14. Procedimiento para revisar una fase antes de empezar la siguiente

1. Revisar la documentación y el estado del repositorio.
2. Verificar que los entregables de la fase actual están completos y coherentes.
3. Confirmar que no hay contradicciones importantes con el plan maestro.
4. Marcar la fase como lista para pasar a la siguiente solo si los criterios de aceptación están cubiertos.
5. Documentar los riesgos o pendientes antes de avanzar.

## 15. Procedimiento de cierre de tarea

1. Revisar git diff.
2. Ejecutar git diff --check.
3. Ejecutar las verificaciones aplicables según la tarea.
4. Ejecutar git status.
5. Informar de archivos nuevos, modificados y comprobaciones fallidas.
