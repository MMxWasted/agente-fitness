# Roadmap de Agente Fitness

Este roadmap es una referencia viva para la ejecución del proyecto. Su propósito es traducir la visión del producto en fases verificables y evitar asumir funcionalidades como implementadas antes de que exista evidencia documental o técnica suficiente.

## Leyenda

- [ ] Pendiente
- [~] En progreso
- [x] Finalizado
- [!] Bloqueado

## Fase 0. Planificación

- Estado: [x] Finalizado
- Objetivo: definir la visión, el alcance y las reglas de trabajo del proyecto.
- Entregables: visión inicial, alcance del MVP, riesgos, principios y estructura documental.
- Dependencias: documentación base y alineación del equipo.
- Criterios de finalización: el alcance del MVP y las principales reglas del proyecto quedan descritos y pueden servir de referencia para la siguiente fase.
- Tareas:
  - [x] Consolidar la visión del producto en el plan maestro.
  - [x] Definir principios de producto y arquitectura.
  - [x] Identificar alcance del MVP y de las funcionalidades posteriores.
  - [x] Documentar riesgos y límites de salud, privacidad y seguridad.

## Fase 1. Documentación fundacional

- Estado: [~] En progreso
- Objetivo: dejar una base documental clara, coherente y reutilizable.
- Entregables: documentos de principios, roadmap, glosario, convenciones, workflow de Codex y la documentación adicional prevista en el plan maestro.
- Dependencias: fase 0.
- Criterios de finalización: los documentos principales del repositorio están presentes, enlazados y coherentes entre sí, y las piezas documentales pendientes quedan identificadas con claridad.
- Tareas:
  - [x] Crear este roadmap.
  - [x] Crear el documento de principios.
  - [x] Crear el glosario de dominio.
  - [x] Crear las convenciones de trabajo.
  - [x] Crear el workflow de Codex.
  - [x] Actualizar la portada del repositorio con enlaces a la documentación relevante.
  - [x] Crear CONTRIBUTING.md.
  - [x] Crear CHANGELOG.md.
  - [x] Documentar la visión y el alcance detallados.
  - [x] Documentar historias de usuario.
  - [ ] Documentar la arquitectura general.
  - [ ] Documentar el modelo de datos detallado.
  - [ ] Documentar seguridad y privacidad.
  - [ ] Documentar los ADR iniciales.

## Fase 2. Fundación técnica

- Estado: [ ] Pendiente
- Objetivo: preparar la base técnica del proyecto sin asumir una implementación funcional completa.
- Entregables: estructura real del monorepo, frontend React con TypeScript, backend FastAPI, PostgreSQL, Docker Compose, Alembic, variables de entorno, linting, tipos y pruebas, GitHub Actions, endpoint GET /health, página inicial mínima y arranque reproducible documentado.
- Dependencias: fase 1.
- Criterios de finalización: el equipo puede iniciar el desarrollo con un entorno reproducible y una visión clara de la arquitectura.
- Tareas:
  - [ ] Crear la estructura real del monorepo.
  - [ ] Inicializar frontend React con TypeScript.
  - [ ] Inicializar backend FastAPI.
  - [ ] Configurar PostgreSQL.
  - [ ] Configurar Docker Compose.
  - [ ] Configurar Alembic.
  - [ ] Configurar variables de entorno.
  - [ ] Configurar linting, tipos y pruebas.
  - [ ] Configurar GitHub Actions.
  - [ ] Implementar GET /health.
  - [ ] Crear una página inicial mínima que compruebe el estado de la API.
  - [ ] Documentar y verificar el arranque reproducible.

## Fase 3. Autenticación y perfil

- Estado: [ ] Pendiente
- Objetivo: permitir que un usuario cree una cuenta, acceda al sistema y gestione su perfil básico.
- Entregables: registro, inicio de sesión, cierre de sesión, perfil fitness y configuración básica.
- Dependencias: fase 2.
- Criterios de finalización: un usuario puede registrarse, autenticarse y consultar su propio perfil sin acceder a datos de otros usuarios.
- Tareas:
  - [ ] Implementar autenticación.
  - [ ] Implementar gestión de sesión.
  - [ ] Implementar perfil fitness.
  - [ ] Implementar validación y autorización por propietario.

## Fase 4. Catálogo de ejercicios

- Estado: [ ] Pendiente
- Objetivo: soportar ejercicios globales y personalizados con información básica de dominio.
- Entregables: catálogo de ejercicios, filtros básicos y creación de ejercicios personalizados.
- Dependencias: fase 3.
- Criterios de finalización: el sistema permite consultar ejercicios y crear ejercicios propios con restricciones claras.
- Tareas:
  - [ ] Definir el modelo de ejercicios.
  - [ ] Implementar búsqueda y filtrado básico.
  - [ ] Implementar ejercicios personalizados.
  - [ ] Implementar reglas de propiedad y acceso.

## Fase 5. Rutinas

- Estado: [ ] Pendiente
- Objetivo: permitir crear y gestionar rutinas de entrenamiento con estructura básica.
- Entregables: rutinas, días, ejercicios planificados, series, repeticiones, RIR/RPE y reglas de progreso básicas.
- Dependencias: fase 4.
- Criterios de finalización: un usuario puede crear una rutina, revisarla y activarla de forma explícita.
- Tareas:
  - [ ] Definir el modelo de rutinas.
  - [ ] Implementar creación y edición de rutinas.
  - [ ] Implementar activación y archivado.
  - [ ] Implementar reglas para una única rutina activa por usuario.

## Fase 6. Registro de entrenamientos

- Estado: [ ] Pendiente
- Objetivo: registrar sesiones reales y conservar un historial estructurado.
- Entregables: sesiones, ejercicios completados, series y notas.
- Dependencias: fase 5.
- Criterios de finalización: un usuario puede iniciar una sesión, registrar series y finalizarla sin perder su historial.
- Tareas:
  - [ ] Definir el modelo de sesiones y series.
  - [ ] Implementar inicio y finalización de sesión.
  - [ ] Implementar registro de series y notas.
  - [ ] Implementar estabilidad histórica frente a cambios de rutina.

## Fase 7. Peso, medidas y analítica

- Estado: [ ] Pendiente
- Objetivo: capturar peso, medidas corporales y métricas objetivas deterministas.
- Entregables: mediciones, tendencia de peso, adherencia, volumen y métricas básicas.
- Dependencias: fase 6.
- Criterios de finalización: el sistema puede mostrar métricas básicas con una definición clara y datos conocidos.
- Tareas:
  - [ ] Definir las métricas deterministas iniciales.
  - [ ] Implementar registro de peso y medidas.
  - [ ] Implementar cálculos básicos de seguimiento.
  - [ ] Implementar pruebas sobre datos de ejemplo.

## Fase 8. Generador determinista de rutinas

- Estado: [ ] Pendiente
- Objetivo: generar borradores de rutina a partir de reglas explícitas y contexto del usuario.
- Entregables: motor determinista de generación de rutinas y salida explicable.
- Dependencias: fase 7.
- Criterios de finalización: el sistema puede producir un borrador de rutina revisable y no activarlo automáticamente.
- Tareas:
  - [ ] Definir las entradas del generador.
  - [ ] Definir las reglas de generación.
  - [ ] Implementar generación de borradores.
  - [ ] Implementar revisión y confirmación del usuario.

## Fase 9. Agente Fitness

- Estado: [ ] Pendiente
- Objetivo: incorporar un asistente controlado para explicar tendencias y proponer acciones.
- Entregables: agente con herramientas limitadas, respuestas estructuradas y confirmación explícita para cambios sensibles.
- Dependencias: fase 8.
- Criterios de finalización: el agente puede consultar información autorizada, explicar hallazgos y guardar recomendaciones sin modificar datos sensibles automáticamente.
- Tareas:
  - [ ] Definir el alcance del agente en el MVP.
  - [ ] Definir herramientas internas y guardrails.
  - [ ] Implementar respuestas estructuradas.
  - [ ] Implementar confirmación para acciones críticas.

## Fase 10. Nutrición básica

- Estado: [ ] Pendiente
- Objetivo: permitir registrar datos nutricionales básicos y utilizarlos como contexto del seguimiento.
- Entregables: registro de calorías y macronutrientes, resúmenes básicos y contexto para el agente.
- Dependencias: fase 7.
- Criterios de finalización: el usuario puede registrar información nutricional básica y consultarla con claridad.
- Tareas:
  - [ ] Definir el modelo mínimo de nutrición.
  - [ ] Implementar registro de datos nutricionales.
  - [ ] Implementar resúmenes básicos.
  - [ ] Definir límites del uso del agente sobre nutrición.

## Fase 11. Endurecimiento

- Estado: [ ] Pendiente
- Objetivo: consolidar la calidad, seguridad y preparación del producto para una primera versión útil.
- Entregables: pruebas, documentación final, revisión de privacidad y preparación de lanzamiento.
- Dependencias: fases 8, 9 y 10.
- Criterios de finalización: el MVP puede presentarse como una solución verificable, segura y documentada.
- Tareas:
  - [ ] Revisar seguridad, privacidad y salud.
  - [ ] Ejecutar pruebas de integración y de aceptación.
  - [ ] Revisar documentación final.
  - [ ] Preparar estrategia de despliegue y soporte inicial.
