# Plan maestro del proyecto Agente Fitness

## Documentación complementaria

Este documento conserva la visión general y el alcance del proyecto. La documentación operativa y de detalle se encuentra distribuida en:

* [Principios](PRINCIPIOS.md)
* [Roadmap](ROADMAP.md)
* [Glosario](GLOSARIO.md)
* [Convenciones](CONVENCIONES.md)
* [Workflow de Codex](CODEX_WORKFLOW.md)

## 1. Visión del producto

Agente Fitness será una aplicación web orientada al registro, seguimiento y análisis de la actividad física del usuario.

Permitirá centralizar información relacionada con:

* Perfil físico y experiencia de entrenamiento.
* Objetivos deportivos y de composición corporal.
* Rutinas de entrenamiento.
* Ejercicios.
* Sesiones realizadas.
* Series, repeticiones y cargas.
* RIR o RPE.
* Peso corporal.
* Medidas corporales.
* Alimentación y macronutrientes.
* Adherencia.
* Evolución del rendimiento.
* Recomendaciones personalizadas.

La aplicación incorporará progresivamente un agente de inteligencia artificial capaz de consultar los datos registrados mediante herramientas internas controladas.

El agente podrá explicar tendencias, detectar posibles estancamientos, generar borradores de rutinas y proponer ajustes. No deberá inventar métricas ni modificar información importante sin la confirmación explícita del usuario.

Codex se utilizará como agente de desarrollo del proyecto, mientras que el Agente Fitness será una funcionalidad integrada dentro de la aplicación.

---

## 2. Objetivos principales

Los principales objetivos del proyecto son:

1. Permitir que el usuario registre sus entrenamientos de forma sencilla.
2. Conservar un historial estructurado de su evolución.
3. Calcular métricas objetivas mediante código determinista.
4. Generar rutinas adaptadas a las necesidades del usuario.
5. Analizar carga, volumen, frecuencia, adherencia y progresión.
6. Registrar peso, medidas y datos nutricionales.
7. Facilitar la interpretación de los datos mediante un agente conversacional.
8. Mantener una arquitectura ampliable y correctamente documentada.
9. Garantizar la privacidad y la propiedad de los datos.
10. Evitar que el modelo de lenguaje realice diagnósticos médicos o invente información.

---

## 3. Principios de diseño

### 3.1 Datos antes que inteligencia artificial

Las métricas principales se calcularán mediante servicios deterministas.

El modelo de lenguaje no deberá calcular directamente:

* Volumen de entrenamiento.
* Número de series semanales.
* Frecuencia por grupo muscular.
* Récords personales.
* Evolución de cargas.
* Evolución del peso.
* Medias móviles.
* Adherencia.
* Comparaciones entre periodos.
* Estimaciones de una repetición máxima.
* Tendencias de medidas corporales.
* Consumo medio de calorías o macronutrientes.

El agente recibirá estos resultados mediante herramientas internas.

### 3.2 Separación de responsabilidades

La aplicación estará dividida en:

* Interfaz de usuario.
* API.
* Servicios de dominio.
* Repositorios de acceso a datos.
* Motor de analítica.
* Motor de generación de rutinas.
* Agente de inteligencia artificial.
* Base de datos.

Los endpoints no deberán contener directamente lógica de negocio compleja.

### 3.3 Acceso controlado del agente

El agente no tendrá acceso directo a PostgreSQL ni podrá ejecutar consultas SQL arbitrarias.

Solo podrá acceder a los datos mediante herramientas autorizadas, por ejemplo:

* Obtener el perfil del usuario.
* Obtener el objetivo activo.
* Obtener la rutina activa.
* Consultar entrenamientos recientes.
* Consultar progresión por ejercicio.
* Consultar tendencias corporales.
* Generar un borrador de rutina.
* Guardar una recomendación.

### 3.4 Recomendaciones explicables

Toda recomendación deberá incluir, cuando sea posible:

* Datos utilizados.
* Tendencia observada.
* Acción recomendada.
* Motivo de la recomendación.
* Información que falta.
* Nivel de confianza.
* Indicación de si requiere confirmación.

### 3.5 Control del usuario

El agente no modificará automáticamente:

* La rutina activa.
* Los objetivos.
* Las cargas planificadas.
* Los datos históricos.
* Las mediciones corporales.
* Los registros nutricionales.
* Las restricciones del usuario.

Primero deberá generar una propuesta que el usuario pueda revisar.

### 3.6 Seguridad y privacidad

La aplicación deberá aplicar:

* Autenticación segura.
* Autorización por propietario.
* Validación de entradas.
* Protección de contraseñas.
* Gestión segura de secretos.
* Reducción de datos sensibles en registros.
* Exportación de datos.
* Eliminación de cuenta.
* Separación entre datos de diferentes usuarios.

---

## 4. Alcance del MVP

El MVP deberá proporcionar un flujo funcional completo desde la creación del perfil hasta el análisis básico del progreso.

### 4.1 Cuenta y autenticación

* Registro.
* Inicio de sesión.
* Renovación de sesión.
* Cierre de sesión.
* Consulta del usuario autenticado.
* Eliminación de cuenta.
* Exportación básica de datos.

### 4.2 Perfil fitness

* Nombre visible.
* Fecha de nacimiento opcional.
* Altura opcional.
* Nivel de experiencia.
* Sistema de unidades.
* Zona horaria.

Objetivos, disponibilidad, duración, equipamiento, preferencias, limitaciones
y ejercicios excluidos pertenecen a entidades o bloques separados y no forman
parte de `UserProfile`.

Peso, composición corporal, pliegues y perímetros tampoco forman parte de
`UserProfile`. El bloque independiente `3B.2 — Historial de mediciones
corporales e importación desde Excel` empieza en 3B.2A con una previsualización
segura y sin persistencia. 3B.2B los modelará mediante entidades históricas
separadas y privadas, sin columnas JSON genéricas ni acoplamiento del perfil al
formato de una hoja concreta.

### 4.3 Objetivos

* Crear un objetivo.
* Consultar el objetivo activo.
* Editar un objetivo.
* Archivar un objetivo.
* Definir fechas y valores objetivo cuando corresponda.

### 4.4 Catálogo de ejercicios

Cada ejercicio podrá contener:

* Nombre.
* Grupo muscular principal.
* Músculos secundarios.
* Patrón de movimiento.
* Tipo de ejercicio.
* Equipamiento.
* Dificultad.
* Instrucciones.
* Alternativas.
* Indicador de ejercicio global o personalizado.

El usuario podrá:

* Buscar ejercicios.
* Filtrar por músculo.
* Filtrar por equipamiento.
* Filtrar por patrón de movimiento.
* Consultar detalles.
* Crear ejercicios personalizados.

### 4.5 Rutinas

El usuario podrá:

* Crear una rutina manual.
* Añadir días.
* Ordenar días.
* Añadir ejercicios.
* Ordenar ejercicios.
* Definir series.
* Definir rangos de repeticiones.
* Definir RIR objetivo.
* Definir descanso.
* Añadir notas.
* Duplicar una rutina.
* Activar una rutina.
* Archivar una rutina.
* Consultar versiones anteriores.

Solo podrá existir una rutina activa por usuario.

### 4.6 Registro de entrenamientos

El usuario podrá:

* Seleccionar un día de su rutina.
* Iniciar una sesión.
* Registrar ejercicios.
* Registrar calentamientos.
* Registrar series efectivas.
* Introducir peso.
* Introducir repeticiones.
* Introducir RIR o RPE.
* Marcar series como completadas o fallidas.
* Añadir notas.
* Omitir un ejercicio.
* Sustituir un ejercicio.
* Dejar una sesión en progreso.
* Finalizar una sesión.
* Consultar el resumen.
* Consultar el historial.

### 4.7 Peso y medidas corporales

3B.2A permite analizar manualmente un XLSX conocido y previsualizar las
revisiones sin guardar el archivo ni los valores. 3B.2B deberá representar una
sesión por revisión fechada. Cada sesión podrá contener valores normalizados
por tipo de métrica, categoría, lado izquierdo, derecho o no aplicable y
unidad. Entre las mediciones previstas están:

* Peso.
* Datos de bioimpedancia.
* Pliegues de plicómetro.
* Perímetros corporales.
* Valores bilaterales cuando corresponda.

La previsualización utiliza un adaptador versionado, hace visibles fechas o
unidades ambiguas y calcula un fingerprint normalizado. La confirmación futura
deberá reanalizar el Excel, comprobar ese fingerprint, ser idempotente, detectar
nuevas columnas de revisión y conservar procedencia y fecha sin asumir que el
archivo es la fuente permanente ni acoplar el frontend a su estructura. La
aplicación podrá mostrar posteriormente:

* Evolución temporal.
* Comparación entre fechas.
* Media móvil del peso.
* Cambios absolutos.
* Cambios porcentuales cuando tengan sentido.

La analítica corporal determinista permanece fuera de 3B.2B y corresponde a
3B.2C. La sincronización con OneDrive y la integración con entrenamientos se
mantienen para bloques posteriores.

### 4.8 Analítica básica

La aplicación calculará:

* Número de entrenamientos.
* Adherencia semanal.
* Duración media.
* Volumen por ejercicio.
* Volumen por grupo muscular.
* Frecuencia semanal.
* Evolución de cargas.
* Evolución de repeticiones.
* Récords personales.
* Tendencia del peso.
* Comparación entre periodos.

### 4.9 Motor de generación de rutinas

La primera versión del generador utilizará reglas deterministas.

Recibirá:

* Objetivo.
* Experiencia.
* Días disponibles.
* Tiempo por sesión.
* Equipamiento.
* Preferencias.
* Limitaciones.
* Ejercicios excluidos.
* Historial disponible.

Generará:

* Distribución semanal.
* Días.
* Ejercicios.
* Series.
* Rangos de repeticiones.
* RIR.
* Descansos.
* Reglas de progresión.
* Explicación de las decisiones.
* Advertencias.
* Borrador revisable.

La rutina no se activará automáticamente.

### 4.10 Agente Fitness inicial

El primer agente podrá:

* Generar un resumen semanal.
* Analizar entrenamientos recientes.
* Explicar tendencias.
* Consultar progresión por ejercicio.
* Consultar adherencia.
* Consultar evolución del peso.
* Proponer ajustes.
* Solicitar un borrador al motor de rutinas.
* Guardar recomendaciones.
* Indicar cuándo faltan datos.

---

## 5. Funcionalidades posteriores

Las siguientes funcionalidades podrán incorporarse después del MVP:

* Aplicación móvil nativa.
* Progressive Web App avanzada.
* Integración con Health Connect.
* Integración con Apple Health.
* Integración con Google Fit.
* Integración con relojes y pulseras.
* Importación desde otras aplicaciones.
* Fotografías de progreso.
* Notificaciones.
* Temporizador de descansos.
* Asistente por voz.
* Reconocimiento de alimentos.
* Escaneo de códigos de barras.
* Catálogo nutricional externo.
* Planificación de comidas.
* Gestión de clientes por entrenadores.
* Grupos o funciones sociales.
* Pagos y suscripciones.
* Comparaciones avanzadas.
* Predicción de rendimiento.
* Análisis de técnica mediante vídeo.
* Arquitectura multiagente.
* Integraciones con calendarios.
* Informes descargables.

Estas funcionalidades no deberán condicionar innecesariamente la primera arquitectura.

---

## 6. Elementos fuera de alcance

Inicialmente quedarán fuera de alcance:

* Diagnóstico de lesiones.
* Diagnóstico de enfermedades.
* Tratamiento médico.
* Prescripción farmacológica.
* Recomendaciones médicas personalizadas.
* Dietas terapéuticas.
* Tratamiento de trastornos de la conducta alimentaria.
* Sustitución de profesionales sanitarios.
* Modificaciones autónomas sin confirmación.
* Garantías de resultados físicos.
* Seguimiento clínico.
* Evaluación biomecánica profesional.
* Uso del agente como fuente única para decisiones de salud.

---

## 7. Arquitectura tecnológica propuesta

### 7.1 Frontend

Tecnologías propuestas:

* React.
* TypeScript.
* Vite.
* React Router.
* TanStack Query.
* React Hook Form.
* Zod.
* Vitest.
* Testing Library.
* Playwright para pruebas end-to-end.
* ESLint.
* Prettier si se decide incorporarlo.

Principios:

* Diseño mobile-first.
* Componentes accesibles.
* Separación por funcionalidades.
* Gestión centralizada de llamadas a la API.
* Estados de carga, error y éxito.
* Validación compartida cuando sea posible.
* No almacenar secretos.
* No llamar directamente a OpenAI.

### 7.2 Backend

Tecnologías propuestas:

* Python.
* FastAPI.
* Pydantic.
* SQLAlchemy.
* Alembic.
* PostgreSQL.
* pytest.
* Ruff.
* mypy.
* OpenAI Agents SDK.
* uv para gestión de dependencias.

Principios:

* Endpoints ligeros.
* Servicios de dominio.
* Repositorios de acceso a datos.
* Esquemas separados de los modelos de persistencia.
* Transacciones para operaciones compuestas.
* Validación de propiedad de datos.
* Pruebas unitarias y de integración.
* Dependencias inyectables.
* Configuración mediante variables de entorno.

### 7.3 Base de datos

Se utilizará PostgreSQL.

Motivos principales:

* Relaciones claras entre entidades.
* Restricciones de integridad.
* Transacciones.
* Consultas históricas.
* Agregaciones.
* Migraciones.
* Índices.
* Posibilidad de utilizar JSONB cuando sea necesario.
* Buen soporte desde SQLAlchemy.

### 7.4 Infraestructura

Se utilizarán inicialmente:

* Docker Compose para desarrollo.
* PostgreSQL en contenedor.
* Backend en contenedor.
* Frontend ejecutable localmente o en contenedor.
* GitHub Actions.
* Archivo `.env.example`.
* Gestión de secretos fuera del repositorio.

### 7.5 Repositorio

Se utilizará un monorepo con:

* Frontend.
* Backend.
* Documentación.
* Scripts.
* Configuración de infraestructura.
* Flujos de integración continua.

---

## 8. Arquitectura funcional

```text
Usuario
   │
   ▼
Frontend React
   │
   ▼
API FastAPI
   ├── Autenticación
   ├── Usuarios y perfiles
   ├── Objetivos
   ├── Catálogo de ejercicios
   ├── Rutinas
   ├── Entrenamientos
   ├── Medidas corporales
   ├── Nutrición
   ├── Analítica determinista
   ├── Motor de generación de rutinas
   └── Orquestador del Agente Fitness
          ├── Herramientas de lectura
          ├── Herramientas de análisis
          ├── Herramientas de generación
          ├── Guardrails
          └── OpenAI Agents SDK
   │
   ▼
PostgreSQL
```

---

## 9. Modelo de datos inicial

El modelo definitivo deberá validarse antes de crear las primeras migraciones.

### 9.1 User

* `id`
* `email`
* `password_hash`
* `is_active`
* `created_at`
* `updated_at`
* `deleted_at`

Estado de 3A.1: la identidad técnica implementa todos los campos anteriores
salvo `deleted_at`; el borrado lógico continúa aplazado y no forma parte de la
primera migración de usuarios.

### 9.1.1 AuthSession

* `id`
* `user_id`
* `refresh_token_hash`
* `created_at`
* `updated_at`
* `expires_at`
* `revoked_at`

Estado de 3A.2: la sesión renovable almacena únicamente el digest SHA-256 del
refresh token opaco. La clave foránea hacia `User` usa borrado en cascada, la
rotación sustituye el digest con bloqueo transaccional y logout marca la
revocación. La expiración es absoluta y la limpieza de sesiones caducadas es
oportunista.

### 9.2 UserProfile

* `id`
* `user_id`
* `display_name`
* `birth_date`
* `height_cm`
* `experience_level`
* `timezone`
* `unit_system`
* `created_at`
* `updated_at`

Estado de 3B.1: `UserProfile` implementa exclusivamente estos campos. Fecha de
nacimiento y altura son opcionales; experiencia, zona horaria y unidades son
obligatorias y no se infieren. La propiedad procede del access token, la
relación con `User` es uno a uno y usa borrado en cascada. Los módulos de
objetivos, disponibilidad, preferencias, equipamiento y limitaciones continúan
separados y pendientes.

### 9.2.1 BodyMeasurementReview y BodyMeasurementValue

Persistencia futura de 3B.2B, todavía no implementada. 3B.2A solo materializa
la lectura segura y el contrato de previsualización:

* `BodyMeasurementReview` representará una revisión fechada y conservará su
  propietario y procedencia.
* `BodyMeasurementValue` representará cada observación normalizada por tipo de
  métrica, categoría, lado y unidad.
* Las entidades tendrán dimensión temporal propia y estarán separadas de
  `UserProfile`; no serán columnas adicionales ni un documento JSON genérico.
* La propiedad privada se relacionará con `User` o `UserProfile`, pero siempre
  se resolverá desde el usuario autenticado.
* Una clave de procedencia estable deberá permitir importación idempotente y
  detección de nuevas revisiones sin duplicar las existentes.
* La confirmación deberá volver a analizar el archivo y comparar el fingerprint
  con la previsualización; el Excel original no se conservará.
* No se define todavía un esquema definitivo, confirmación, sincronización,
  analítica ni integración con OneDrive.

### 9.3 UserEquipment

* `id`
* `user_id`
* `equipment_type`
* `notes`

### 9.4 FitnessGoal

* `id`
* `user_id`
* `goal_type`
* `target_value`
* `start_date`
* `target_date`
* `status`
* `notes`
* `created_at`
* `updated_at`

### 9.5 Exercise

* `id`
* `name`
* `slug`
* `primary_muscle`
* `movement_pattern`
* `equipment`
* `difficulty`
* `instructions`
* `is_global`
* `created_by_user_id`
* `created_at`
* `updated_at`

### 9.6 ExerciseSecondaryMuscle

* `exercise_id`
* `muscle_group`

### 9.7 ExerciseAlternative

* `exercise_id`
* `alternative_exercise_id`
* `reason`

### 9.8 UserExcludedExercise

* `user_id`
* `exercise_id`
* `reason`

### 9.9 Routine

* `id`
* `user_id`
* `name`
* `objective`
* `status`
* `version`
* `parent_routine_id`
* `created_at`
* `updated_at`
* `archived_at`

### 9.10 RoutineDay

* `id`
* `routine_id`
* `name`
* `position`
* `estimated_duration_minutes`

### 9.11 RoutineExercise

* `id`
* `routine_day_id`
* `exercise_id`
* `position`
* `planned_sets`
* `minimum_repetitions`
* `maximum_repetitions`
* `target_rir`
* `rest_seconds`
* `progression_rule`
* `notes`

### 9.12 WorkoutSession

* `id`
* `user_id`
* `routine_id`
* `routine_day_id`
* `started_at`
* `completed_at`
* `duration_seconds`
* `status`
* `session_rpe`
* `notes`
* `created_at`
* `updated_at`

### 9.13 WorkoutExercise

* `id`
* `workout_session_id`
* `exercise_id`
* `routine_exercise_id`
* `position`
* `was_substituted`
* `substituted_exercise_id`
* `notes`

### 9.14 SetLog

* `id`
* `workout_exercise_id`
* `set_number`
* `set_type`
* `weight_kg`
* `repetitions`
* `rir`
* `rpe`
* `completed`
* `is_personal_record`
* `created_at`
* `updated_at`

### 9.15 BodyMeasurement

* `id`
* `user_id`
* `measurement_date`
* `weight_kg`
* `body_fat_percentage`
* `waist_cm`
* `chest_cm`
* `arm_cm`
* `thigh_cm`
* `hip_cm`
* `notes`
* `created_at`
* `updated_at`

### 9.16 NutritionLog

* `id`
* `user_id`
* `log_date`
* `calories`
* `protein_g`
* `carbohydrates_g`
* `fat_g`
* `fiber_g`
* `water_ml`
* `notes`
* `created_at`
* `updated_at`

### 9.17 AgentConversation

* `id`
* `user_id`
* `title`
* `created_at`
* `updated_at`

### 9.18 AgentMessage

* `id`
* `conversation_id`
* `role`
* `content`
* `created_at`

No se almacenará razonamiento interno del modelo.

### 9.19 AgentRecommendation

* `id`
* `user_id`
* `conversation_id`
* `recommendation_type`
* `summary`
* `explanation`
* `evidence`
* `confidence`
* `status`
* `requires_confirmation`
* `created_at`
* `reviewed_at`

### 9.20 AgentToolExecution

* `id`
* `conversation_id`
* `tool_name`
* `status`
* `duration_ms`
* `created_at`

No almacenará datos sensibles completos salvo que exista una razón documentada.

---

## 10. Restricciones principales del modelo de datos

Deberán contemplarse las siguientes restricciones:

* El correo será único.
* Cada perfil pertenecerá a un usuario.
* Un usuario solo podrá acceder a sus propios registros.
* Solo podrá existir una rutina activa por usuario.
* La edición de una rutina no deberá alterar entrenamientos históricos.
* Las series históricas conservarán los valores registrados.
* Una sesión finalizada no se modificará libremente sin un mecanismo explícito.
* Las mediciones corporales deberán tener una fecha válida.
* Los ejercicios globales no podrán ser modificados por usuarios normales.
* Los ejercicios personalizados pertenecerán al usuario que los creó.
* Las recomendaciones deberán conservar las evidencias utilizadas.
* Las acciones destructivas deberán ser auditables cuando sea necesario.
* Las eliminaciones deberán respetar las relaciones históricas.
* La zona horaria del usuario deberá considerarse en agrupaciones diarias y semanales.

---

## 11. Motor determinista de generación de rutinas

### 11.1 Entradas

* Objetivo.
* Experiencia.
* Días disponibles.
* Tiempo por sesión.
* Equipamiento.
* Preferencias.
* Limitaciones.
* Ejercicios excluidos.
* Volumen anterior.
* Historial de rendimiento.
* Frecuencia deseada.

### 11.2 Proceso

1. Validar los datos de entrada.
2. Elegir una distribución semanal.
3. Determinar la frecuencia por grupo muscular.
4. Asignar un volumen inicial.
5. Seleccionar patrones de movimiento.
6. Seleccionar ejercicios compatibles.
7. Distribuir los ejercicios entre los días.
8. Definir series y rangos de repeticiones.
9. Definir RIR objetivo.
10. Definir descansos.
11. Añadir reglas de progresión.
12. Estimar la duración.
13. Validar equilibrio y compatibilidad.
14. Generar una explicación.
15. Crear un borrador.
16. Solicitar confirmación antes de activarlo.

### 11.3 Ejemplo de regla de progresión

Cuando el usuario complete todas las series en el límite superior del rango de repeticiones, manteniendo el RIR objetivo durante el número de sesiones establecido, el sistema podrá proponer un incremento de carga.

La regla exacta deberá ser configurable y estar cubierta por pruebas.

### 11.4 Validaciones

El motor deberá comprobar:

* Compatibilidad con el equipamiento.
* Ejercicios excluidos.
* Duración aproximada.
* Repetición excesiva de patrones.
* Equilibrio entre grupos musculares.
* Volumen razonable según experiencia.
* Descanso suficiente.
* Frecuencia compatible con los días disponibles.
* Existencia de datos suficientes.

---

## 12. Diseño inicial del Agente Fitness

### 12.1 Arquitectura inicial

Se utilizará inicialmente un único agente orquestador.

Nombre interno propuesto:

```text
FitnessCoachAgent
```

No se utilizará una arquitectura multiagente hasta que exista una necesidad real y medible.

### 12.2 Responsabilidades

El agente podrá:

* Interpretar la petición del usuario.
* Consultar el contexto autorizado.
* Seleccionar herramientas.
* Explicar tendencias.
* Proponer acciones.
* Generar borradores.
* Indicar incertidumbre.
* Identificar información insuficiente.
* Aplicar guardrails.
* Solicitar confirmación antes de cambios relevantes.

### 12.3 Herramientas iniciales

Herramientas de lectura:

```text
get_user_context()
get_active_goal()
get_active_routine()
get_recent_workouts(days)
get_exercise_history(exercise_id, weeks)
get_weekly_training_volume(weeks)
get_strength_trends(weeks)
get_body_weight_trend(days)
get_measurement_comparison(start_date, end_date)
get_training_adherence(weeks)
get_nutrition_summary(days)
```

Herramientas de generación:

```text
generate_routine_draft(parameters)
generate_progression_proposal(parameters)
generate_weekly_summary(parameters)
```

Herramientas de persistencia controlada:

```text
save_agent_recommendation(recommendation)
```

Las herramientas que modifiquen objetivos, rutinas o registros deberán implementarse posteriormente y exigir confirmación explícita.

### 12.4 Salida estructurada

La respuesta del agente deberá validarse con un esquema similar a:

```json
{
  "summary": "Resumen de la situación",
  "observations": [
    {
      "metric": "Volumen de pectoral",
      "finding": "Ha aumentado durante tres semanas",
      "evidence": "12, 14 y 16 series semanales"
    }
  ],
  "recommendations": [
    {
      "action": "Mantener el volumen actual",
      "reason": "Existe progresión sin caída de rendimiento",
      "priority": "medium"
    }
  ],
  "missing_information": [],
  "confidence": 0.82,
  "requires_confirmation": false
}
```

### 12.5 Confirmación obligatoria

Requerirán confirmación explícita:

* Activar una rutina.
* Sustituir la rutina activa.
* Modificar un objetivo.
* Cambiar cargas planificadas.
* Eliminar registros.
* Editar datos históricos.
* Guardar una nueva restricción.
* Aplicar un cambio nutricional persistente.
* Compartir o exportar datos.

---

## 13. Seguridad relacionada con fitness y salud

El agente no deberá diagnosticar.

Cuando el usuario mencione posibles señales graves, deberá priorizar una respuesta segura.

Ejemplos:

* Dolor en el pecho.
* Dificultad respiratoria.
* Desmayo.
* Pérdida de conocimiento.
* Dolor agudo.
* Lesión grave.
* Sangrado.
* Síntomas neurológicos.
* Conductas alimentarias extremas.
* Uso peligroso de sustancias.
* Empeoramiento importante de una lesión.

En estos casos:

1. No deberá emitir un diagnóstico.
2. No deberá recomendar entrenar ignorando los síntomas.
3. Deberá indicar los límites de la aplicación.
4. Deberá recomendar una valoración profesional adecuada.
5. Deberá evitar afirmaciones categóricas sin evidencia.

---

## 14. Estructura propuesta del repositorio

```text
agente-fitness/
├── AGENTS.md
├── README.md
├── LICENSE
├── CHANGELOG.md
├── CONTRIBUTING.md
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Makefile
│
├── frontend/
│   ├── AGENTS.md
│   ├── package.json
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── features/
│   │   │   ├── auth/
│   │   │   ├── profile/
│   │   │   ├── goals/
│   │   │   ├── exercises/
│   │   │   ├── routines/
│   │   │   ├── workouts/
│   │   │   ├── measurements/
│   │   │   ├── nutrition/
│   │   │   ├── analytics/
│   │   │   └── agent/
│   │   ├── services/
│   │   ├── hooks/
│   │   ├── schemas/
│   │   └── tests/
│   └── e2e/
│
├── backend/
│   ├── AGENTS.md
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── repositories/
│   │   ├── services/
│   │   ├── analytics/
│   │   ├── routine_engine/
│   │   ├── agents/
│   │   │   ├── fitness_coach.py
│   │   │   ├── tools/
│   │   │   ├── guardrails/
│   │   │   ├── prompts/
│   │   │   └── output_types/
│   │   └── tests/
│   └── alembic/
│
├── docs/
│   ├── PLAN_MAESTRO.md
│   ├── CODEX_WORKFLOW.md
│   ├── product/
│   │   ├── vision.md
│   │   ├── scope.md
│   │   ├── user-stories.md
│   │   └── roadmap.md
│   ├── architecture/
│   │   ├── overview.md
│   │   ├── data-model.md
│   │   ├── api-design.md
│   │   └── agent-design.md
│   ├── decisions/
│   │   ├── ADR-001-monorepo.md
│   │   ├── ADR-002-postgresql.md
│   │   └── ADR-003-single-agent-first.md
│   ├── development/
│   │   ├── setup.md
│   │   ├── testing.md
│   │   ├── git-workflow.md
│   │   └── definition-of-done.md
│   ├── safety/
│   │   ├── fitness-safety.md
│   │   ├── privacy.md
│   │   └── agent-guardrails.md
│   └── api/
│
├── scripts/
│   ├── seed_exercises.py
│   ├── create_demo_user.py
│   └── export_openapi.py
│
└── .github/
    ├── workflows/
    │   ├── backend-ci.yml
    │   ├── frontend-ci.yml
    │   └── code-quality.yml
    ├── ISSUE_TEMPLATE/
    └── pull_request_template.md
```

Esta estructura es una propuesta y podrá ajustarse mediante decisiones documentadas.

---

## 15. Estrategia Git

### 15.1 Rama principal

* `main`: contiene únicamente versiones estables o estados verificados.

### 15.2 Ramas de trabajo

Formato recomendado:

* `feature/nombre-funcionalidad`
* `fix/nombre-error`
* `docs/nombre-documentacion`
* `refactor/nombre-refactor`
* `test/nombre-prueba`
* `chore/nombre-tarea`

### 15.3 Commits

Se utilizarán mensajes similares a Conventional Commits:

```text
feat: add workout session logging
fix: validate duplicate exercise sets
docs: describe routine generation rules
test: cover progressive overload service
refactor: separate analytics repository
chore: configure backend linting
```

### 15.4 Pull requests

Cada pull request deberá indicar:

* Problema que resuelve.
* Cambios realizados.
* Criterios de aceptación.
* Migraciones.
* Pruebas ejecutadas.
* Capturas cuando afecte a la interfaz.
* Riesgos conocidos.
* Documentación actualizada.
* Trabajo pendiente.

---

## 16. Definition of Done

Una tarea se considerará terminada cuando:

1. Cumpla todos sus criterios de aceptación.
2. No incluya cambios ajenos a la tarea.
3. Tenga validación de entrada.
4. Respete la autorización.
5. Incluya pruebas unitarias relevantes.
6. Incluya pruebas de integración cuando acceda a la base de datos.
7. Incluya pruebas de interfaz para flujos críticos.
8. Supere linting.
9. Supere la comprobación de tipos.
10. Supere el build cuando corresponda.
11. Incluya migraciones cuando sean necesarias.
12. Actualice la documentación.
13. No incluya secretos.
14. No registre información sensible innecesaria.
15. Muestre estados de carga y error en la interfaz.
16. Sea usable desde dispositivos móviles cuando tenga interfaz.
17. Mantenga compatibilidad con datos históricos.
18. Incluya un resumen de los archivos modificados.
19. Incluya los comandos ejecutados.
20. Incluya los resultados de verificación.
21. Declare riesgos o limitaciones pendientes.

---

## 17. Fases de desarrollo

### Fase 0 — Análisis y planificación

Resultado esperado:

* Visión revisada.
* Alcance definido.
* Casos de uso.
* Arquitectura propuesta.
* Modelo de datos inicial.
* Riesgos identificados.
* Roadmap.
* Decisiones ADR pendientes.

No se implementará funcionalidad de negocio.

### Fase 1 — Documentación fundacional

Resultado esperado:

* README.
* AGENTS.
* Contribución.
* Flujo Git.
* Definition of Done.
* Visión.
* Alcance.
* Historias de usuario.
* Arquitectura.
* Modelo de datos.
* Seguridad.
* Privacidad.
* ADR iniciales.

### Fase 2 — Fundación técnica

Resultado esperado:

* Monorepo.
* Frontend React y TypeScript.
* Backend FastAPI.
* PostgreSQL.
* Docker Compose.
* Alembic.
* Calidad de código.
* Integración continua.
* Variables de entorno.
* Endpoint de salud.
* Página inicial mínima.

### Fase 3 — Autenticación y perfil

Resultado esperado:

* Registro.
* Inicio de sesión.
* Renovación de sesión.
* Cierre de sesión.
* Usuario actual.
* Perfil fitness.
* Objetivos.
* Equipamiento.
* Preferencias.
* Limitaciones.
* Pruebas de autorización.

Estado operativo: 3A.1 implementa identidad y access token; 3A.2 implementa la
gestión de sesión web, renovación, revocación e interfaz mínima; 3B.1
implementa el perfil fitness básico privado; 3B.2A implementa lectura segura y
previsualización autenticada de un XLSX conocido sin persistencia. Objetivos,
equipamiento, preferencias, limitaciones y autorización general por
propietario continúan pendientes. 3B.2B gestionará la confirmación idempotente
y el historial privado mediante entidades separadas, incluido el versionado y
la reversión de importaciones propias; 3B.2C cubrirá la analítica corporal
determinista. Ninguna de estas entregas amplía `UserProfile`.

### Fase 4 — Catálogo de ejercicios

Resultado esperado:

* Modelo de ejercicios.
* Datos iniciales.
* Búsqueda.
* Filtros.
* Detalle.
* Ejercicios personalizados.
* Alternativas.
* Interfaz responsive.

### Fase 5 — Rutinas manuales

Resultado esperado:

* Creación.
* Edición.
* Días.
* Ejercicios.
* Orden.
* Series.
* Repeticiones.
* RIR.
* Descanso.
* Duplicación.
* Activación.
* Archivado.
* Versionado.

### Fase 6 — Registro de entrenamientos

Resultado esperado:

* Inicio de sesión.
* Registro de ejercicios.
* Registro de series.
* Autoguardado.
* Sesiones en progreso.
* Finalización.
* Resumen.
* Historial.
* Volumen.
* Récords.

### Fase 7 — Peso, medidas y analítica

Resultado esperado:

* Consumo del historial corporal de 3B.2.
* Media móvil.
* Comparaciones.
* Volumen semanal.
* Frecuencia.
* Adherencia.
* Evolución por ejercicio.
* Récords.
* Panel principal.

### Fase 8 — Generador determinista de rutinas

Resultado esperado:

* Motor de reglas.
* Validaciones.
* Borradores.
* Explicaciones.
* Reglas de progresión.
* Compatibilidad con diferentes días y equipamientos.
* Confirmación antes de activar.

### Fase 9 — Agente Fitness

Resultado esperado:

* OpenAI Agents SDK.
* Herramientas controladas.
* Salidas estructuradas.
* Guardrails.
* Conversaciones.
* Recomendaciones.
* Resumen semanal.
* Pruebas simuladas.
* Evaluaciones.

### Fase 10 — Nutrición básica

Resultado esperado:

* Calorías.
* Macronutrientes.
* Fibra.
* Agua.
* Notas.
* Tendencias.
* Adherencia.
* Herramientas de consulta para el agente.

### Fase 11 — Endurecimiento

Resultado esperado:

* Pruebas end-to-end.
* Seguridad.
* Rendimiento.
* Accesibilidad.
* Privacidad.
* Exportación.
* Eliminación.
* Despliegue.
* Datos de demostración.

### Fase 12 — Versión inicial

Resultado esperado:

* Instalación reproducible.
* Base de datos inicializable.
* Documentación completa.
* Changelog.
* Notas de versión.
* Etiqueta `v0.1.0`.

---

## 18. Decisiones ADR iniciales

Deberán documentarse al menos:

* ADR-001: uso de monorepo.
* ADR-002: elección de PostgreSQL.
* ADR-003: utilización inicial de un único agente.
* ADR-004: separación entre métricas deterministas e inteligencia artificial.
* ADR-005: estrategia de autenticación.
* ADR-006: estrategia de versionado de rutinas.
* ADR-007: conservación de datos históricos.
* ADR-008: gestión de confirmaciones del agente.
* ADR-009: política de almacenamiento de conversaciones.
* ADR-010: estrategia de eliminación y exportación de datos.
* ADR-011: elección de la biblioteca de componentes.
* ADR-012: estrategia de despliegue.

---

## 19. Riesgos principales

### 19.1 Sobreingeniería

Riesgo de añadir demasiadas tecnologías, agentes o integraciones antes de validar el flujo principal.

Mitigación:

* Mantener un único agente.
* Posponer integraciones.
* Implementar por fases.
* Exigir criterios de aceptación.

### 19.2 Métricas inventadas

Riesgo de que el modelo genere datos que no existen.

Mitigación:

* Herramientas estructuradas.
* Servicios deterministas.
* Evidencias.
* Salidas validadas.
* Evaluaciones específicas.

### 19.3 Acceso a datos ajenos

Riesgo de errores de autorización.

Mitigación:

* Validación del usuario en servicios y repositorios.
* Pruebas de propiedad.
* No aceptar identificadores de usuario proporcionados libremente por el agente.

### 19.4 Pérdida de datos históricos

Riesgo de alterar entrenamientos antiguos al editar rutinas.

Mitigación:

* Versionado.
* Copias de los valores planificados relevantes.
* Restricciones de edición.
* Pruebas de integridad histórica.

### 19.5 Recomendaciones relacionadas con salud

Riesgo de que el agente dé recomendaciones inapropiadas.

Mitigación:

* Guardrails.
* Mensajes claros sobre limitaciones.
* Detección de situaciones graves.
* No realizar diagnósticos.
* Evaluaciones de seguridad.

### 19.6 Privacidad

Riesgo derivado del almacenamiento de información física y hábitos personales.

Mitigación:

* Minimización.
* Exportación.
* Eliminación.
* Control de registros.
* Gestión segura de secretos.
* Política de retención.

### 19.7 Dependencia de servicios externos

Riesgo de fallos, costes o cambios en la API del modelo.

Mitigación:

* Separar el agente de la lógica principal.
* Manejar errores y timeouts.
* Mantener funcionalidades deterministas.
* Simular llamadas en pruebas.
* Registrar consumo.

---

## 20. Criterio para incorporar nuevas funcionalidades

Una nueva funcionalidad solo se incorporará al roadmap cuando se haya definido:

* Problema que resuelve.
* Usuario beneficiado.
* Datos necesarios.
* Flujo principal.
* Riesgos.
* Dependencias.
* Criterios de aceptación.
* Pruebas necesarias.
* Impacto en privacidad.
* Prioridad respecto al MVP.
* Métrica para evaluar su utilidad.

No se añadirán funcionalidades únicamente porque sean técnicamente posibles.

---

## 21. Flujo de trabajo con Codex

Cada tarea enviada a Codex deberá:

1. Referirse a una única fase o funcionalidad.
2. Pedirle que lea `AGENTS.md`.
3. Pedirle que inspeccione el código existente.
4. Definir criterios de aceptación.
5. Definir lo que queda fuera de alcance.
6. Solicitar un plan antes de editar en tareas complejas.
7. Exigir pruebas.
8. Exigir linting y comprobación de tipos.
9. Exigir revisión del diff.
10. Exigir actualización documental.
11. Exigir un resumen final verificable.

Codex no deberá ejecutar automáticamente todas las fases del proyecto en una sola tarea.

Cada fase deberá revisarse antes de comenzar la siguiente.
