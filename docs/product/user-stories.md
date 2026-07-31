# Historias de usuario

## AUTH — Cuenta y autenticación

### AUTH-001 — Registro de cuenta

- Historia: Como usuario nuevo, quiero crear una cuenta para conservar mis datos de entrenamiento.
- Prioridad: Must
- Fase: 3
- Dependencias: Fundación técnica
- Estado: Partial — el registro backend está implementado; la interfaz de
  registro orientada al usuario permanece pendiente.

#### Criterios de aceptación

1. El usuario puede proporcionar los datos mínimos requeridos para crear una cuenta.
2. El sistema rechaza un correo ya registrado con un mensaje observable.
3. La contraseña no se almacena en texto plano.
4. Al completarse el registro, el usuario recibe una respuesta observable de éxito o error.

### AUTH-002 — Inicio de sesión

- Historia: Como usuario registrado, quiero iniciar sesión para acceder a mi información personal.
- Prioridad: Must
- Fase: 3
- Dependencias: AUTH-001
- Estado: Completed — inicio y cierre de sesión implementados, validados en el
  pull request #8 y fusionados en `main`.

#### Criterios de aceptación

1. El usuario puede acceder con un correo y una contraseña válidos.
2. El sistema rechaza credenciales inválidas con un mensaje observable.
3. El usuario puede cerrar sesión y perder el acceso a la sesión activa.

## PROF — Perfil fitness

### PROF-001 — Completar perfil básico

- Historia: Como usuario, quiero completar un perfil fitness básico para que el sistema tenga contexto sobre mi situación inicial.
- Prioridad: Must
- Fase: 3
- Dependencias: AUTH-002
- Estado: Completed — implementado, validado por los tres jobs de CI en el
  pull request #10 y fusionado en `main`.

#### Criterios de aceptación

1. El usuario puede introducir los datos básicos solicitados por el perfil.
2. El sistema permite guardar el perfil con información válida.
3. El sistema rechaza valores inválidos con un mensaje observable.
4. El perfil solo puede consultarse y actualizarse mediante la identidad
   autenticada de su propietario.

## GOAL — Objetivos

### GOAL-001 — Definir objetivos

- Historia: Como usuario, quiero establecer objetivos para orientar mi seguimiento y mis rutinas.
- Prioridad: Must
- Fase: 3
- Dependencias: PROF-001
- Estado: Pending

#### Criterios de aceptación

1. El usuario puede crear uno o más objetivos iniciales.
2. El sistema permite ver los objetivos guardados en un momento posterior.
3. El sistema rechaza objetivos incompletos cuando la información requerida no está presente.

## EXER — Catálogo de ejercicios

### EXER-001 — Consultar ejercicios

- Historia: Como usuario, quiero consultar ejercicios para seleccionar los que quiero incluir en mis rutinas.
- Prioridad: Must
- Fase: 4
- Dependencias: PROF-001
- Estado: Pending

#### Criterios de aceptación

1. El usuario puede ver un listado de ejercicios disponibles.
2. El usuario puede filtrar o buscar ejercicios por criterios básicos.
3. El sistema muestra información suficiente para identificar cada ejercicio.

### EXER-002 — Crear ejercicio personalizado

- Historia: Como usuario, quiero crear un ejercicio personalizado para adaptar el catálogo a mi contexto.
- Prioridad: Should
- Fase: 4
- Dependencias: EXER-001
- Estado: Pending

#### Criterios de aceptación

1. El usuario puede crear un ejercicio con los datos mínimos requeridos.
2. El ejercicio creado aparece en el catálogo disponible para ese usuario.
3. El sistema rechaza datos incompletos o inválidos.

## ROUT — Rutinas

### ROUT-001 — Crear rutina

- Historia: Como usuario, quiero crear una rutina para planificar mi semana de entrenamiento.
- Prioridad: Must
- Fase: 5
- Dependencias: EXER-001, GOAL-001
- Estado: Pending

#### Criterios de aceptación

1. El usuario puede crear una rutina con un nombre y estructura básica.
2. La rutina permite incluir ejercicios y cargas previstas.
3. El sistema permite guardar la rutina para su revisión posterior.

### ROUT-002 — Activar rutina

- Historia: Como usuario, quiero activar una rutina para indicar cuál es mi plan actual.
- Prioridad: Must
- Fase: 5
- Dependencias: ROUT-001
- Estado: Pending

#### Criterios de aceptación

1. El usuario puede marcar una rutina como activa.
2. El sistema permite ver claramente cuál rutina está activa.
3. La activación requiere una acción explícita del usuario.

## WORK — Registro de entrenamientos

### WORK-001 — Registrar sesión de entrenamiento

- Historia: Como usuario, quiero registrar una sesión de entrenamiento para conservar un historial real de mi actividad.
- Prioridad: Must
- Fase: 6
- Dependencias: ROUT-002
- Estado: Pending

#### Criterios de aceptación

1. El usuario puede iniciar y finalizar una sesión de entrenamiento.
2. El sistema permite registrar ejercicios, series y notas asociadas a la sesión.
3. La sesión registrada queda accesible posteriormente para su consulta.

### WORK-002 — Mantener historial estable

- Historia: Como usuario, quiero que mis sesiones registradas permanezcan estables para no perder información histórica cuando cambio de rutina.
- Prioridad: Must
- Fase: 6
- Dependencias: WORK-001
- Estado: Pending

#### Criterios de aceptación

1. Los cambios posteriores en una rutina no alteran automáticamente una sesión ya registrada.
2. El usuario puede consultar el historial completo de sesiones registradas.

## MEAS — Peso y medidas

### MEAS-001 — Registrar peso y medidas

- Historia: Como usuario, quiero registrar mi peso y medidas corporales para seguir mi progreso físico.
- Prioridad: Must
- Fase: 7
- Dependencias: AUTH-002
- Estado: Pending

#### Criterios de aceptación

1. El usuario puede introducir registros de peso y medidas corporales.
2. El sistema permite guardar varios registros en distintos momentos.
3. El sistema rechaza entradas incompletas o inválidas.

## ANAL — Analítica

### ANAL-001 — Consultar métricas deterministas

- Historia: Como usuario, quiero consultar métricas deterministas para comprender mejor mi evolución sin depender de interpretaciones ambiguas.
- Prioridad: Must
- Fase: 7
- Dependencias: WORK-001, MEAS-001
- Estado: Pending

#### Criterios de aceptación

1. El usuario puede consultar métricas básicas sobre volumen, adherencia y progreso.
2. El sistema muestra una definición o contexto claro para cada métrica.
3. El sistema permite identificar cuándo no hay datos suficientes para calcular una métrica.

## GENR — Generador determinista de rutinas

### GENR-001 — Generar borrador de rutina

- Historia: Como usuario, quiero recibir un borrador de rutina basado en reglas explícitas para empezar a trabajar con un plan estructurado.
- Prioridad: Must
- Fase: 8
- Dependencias: ANAL-001, ROUT-001
- Estado: Pending

#### Criterios de aceptación

1. El sistema puede producir un borrador de rutina a partir de datos conocidos del usuario.
2. El borrador se presenta como una propuesta revisable.
3. El usuario puede revisar y aceptar o rechazar el borrador.

## AGNT — Agente Fitness

### AGNT-001 — Consultar al agente

- Historia: Como usuario, quiero consultar al Agente Fitness para recibir explicaciones sobre mis datos y propuestas guiadas.
- Prioridad: Must
- Fase: 9
- Dependencias: ANAL-001
- Estado: Pending

#### Criterios de aceptación

1. El usuario puede enviar una consulta relacionada con su información registrada.
2. El agente responde con una explicación basada en datos disponibles.
3. El sistema distingue entre observación, recomendación y propuesta.

### AGNT-002 — Confirmar acciones sensibles

- Historia: Como usuario, quiero confirmar acciones sensibles antes de que se apliquen para mantener el control sobre mis datos.
- Prioridad: Must
- Fase: 9
- Dependencias: AGNT-001
- Estado: Pending

#### Criterios de aceptación

1. El sistema exige una confirmación explícita para cambios sensibles.
2. El usuario puede rechazar una propuesta sin que se aplique ningún cambio.
3. El sistema deja constancia de la propuesta pendiente cuando corresponde.

## NUTR — Nutrición

### NUTR-001 — Registrar nutrición básica

- Historia: Como usuario, quiero registrar datos nutricionales básicos para contextualizar mi seguimiento.
- Prioridad: Should
- Fase: 10
- Dependencias: AUTH-002
- Estado: Pending

#### Criterios de aceptación

1. El usuario puede registrar calorías y macronutrientes básicos.
2. El sistema permite guardar múltiples registros en distintos momentos.
3. El sistema muestra un estado claro cuando no hay datos nutricionales disponibles.

## PRIV — Privacidad y gestión de datos

### PRIV-001 — Gestionar privacidad y datos

- Historia: Como usuario, quiero gestionar mis datos y mi privacidad para mantener el control sobre mi información.
- Prioridad: Must
- Fase: 11
- Dependencias: AUTH-002
- Estado: Pending

#### Criterios de aceptación

1. El usuario puede solicitar una exportación de sus datos.
2. El usuario puede iniciar una eliminación de datos con una acción explícita.
3. El sistema ofrece una respuesta observable de aceptación o error para estas solicitudes.
