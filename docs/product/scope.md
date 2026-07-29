# Alcance del producto

## Objetivo de este documento

Definir de forma clara qué se incluirá y qué se excluirá en la primera fase de desarrollo de Agente Fitness, manteniendo el alcance alineado con la documentación de producto, arquitectura y roadmap.

## Must have

Una funcionalidad clasificada como Must have es prioritaria para el MVP, pero no se considera implementada hasta que exista evidencia verificable en el repositorio.

Los elementos Must have del MVP son:

- autenticación básica para crear y acceder a una cuenta;
- perfil fitness con información básica del usuario;
- objetivos iniciales de entrenamiento o composición corporal;
- catálogo de ejercicios globales y personalizados;
- rutinas con días, ejercicios, series, repeticiones y cargas;
- registro de entrenamientos con sesiones reales y series completadas;
- registro de peso y medidas corporales;
- analítica determinista básica sobre volumen, adherencia, progresión y tendencias;
- generador determinista de rutinas con salida revisable;
- Agente Fitness inicial con herramientas limitadas y respuestas explicables;
- nutrición básica para registrar calorías y macronutrientes;
- privacidad, exportación y eliminación de datos.

## Should have

Estas funcionalidades son importantes, pero no son imprescindibles para validar el flujo principal del MVP:

- mejoras de edición y reorganización de rutinas;
- resúmenes más ricos de progreso y adherencia;
- recomendaciones más contextualizadas sobre carga y recuperación;
- historial de cambios de objetivos o medidas con mayor detalle;
- soporte para más tipos de métricas nutricionales o corporales.

## Could have

Estas mejoras pueden posponerse sin comprometer la comprensión del producto:

- recomendaciones automáticas con mayor grado de personalización;
- vistas de comparación más avanzadas entre periodos;
- soporte para múltiples perfiles o contextos de usuario;
- integración con contenido o guías externas.

## Won't have for MVP

Las siguientes capacidades no formarán parte del MVP:

- aplicación móvil nativa;
- integraciones con wearables;
- funciones sociales;
- pagos;
- arquitectura multiagente;
- reconocimiento de alimentos por imagen;
- análisis de técnica por vídeo;
- dietas terapéuticas;
- diagnóstico médico.

## Flujos imprescindibles del MVP

El MVP debe permitir, como mínimo, los siguientes flujos:

1. crear una cuenta y acceder al sistema;
2. completar un perfil fitness básico;
3. definir objetivos iniciales;
4. crear o revisar una rutina;
5. registrar una sesión de entrenamiento;
6. registrar peso y medidas;
7. consultar métricas deterministas básicas;
8. solicitar una explicación o propuesta al Agente Fitness;
9. gestionar la privacidad y la eliminación de datos.

## Restricciones

- El alcance debe mantenerse alineado con los principios del producto y con la fase documental y técnica actual.
- No se deben introducir funciones que impliquen decisiones clínicas o diagnósticas.
- Las acciones sensibles deben requerir confirmación explícita y no aplicarse automáticamente.
- No se debe presentar ninguna funcionalidad como implementada sin evidencia en el repositorio.

## Dependencias entre módulos

El alcance del MVP depende de la coherencia entre los siguientes módulos:

- autenticación y perfil;
- catálogo de ejercicios y rutinas;
- registro de entrenamientos y métricas;
- analítica determinista;
- Agente Fitness y sus herramientas limitadas;
- gestión de privacidad y datos.

## Criterios generales de éxito

El alcance podrá considerarse adecuado cuando:

- el flujo principal de registro y seguimiento pueda explicarse de forma completa;
- los módulos críticos del MVP puedan verificarse con documentos y criterios claros;
- las prioridades Must/Should/Could queden justificadas frente al objetivo del producto;
- los cambios de alcance puedan registrarse y revisarse sin ambigüedad.

## Procedimiento para controlar cambios de alcance

1. Identificar la propuesta de cambio.
2. Clasificarla como Must, Should, Could o Won't for MVP.
3. Evaluar si afecta a los flujos principales o a la seguridad y privacidad.
4. Registrar la decisión y su justificación antes de modificar el alcance.
5. Actualizar la documentación si el cambio modifica el producto o la fase del roadmap.
