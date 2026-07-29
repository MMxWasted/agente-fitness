# Glosario de Agente Fitness

Este glosario define los términos del dominio que se utilizarán como referencia de trabajo. Algunas definiciones pueden admitir variantes; en este proyecto se adoptará una interpretación concreta y se documentarán las limitaciones correspondientes.

## Repetición

Una repetición es una ejecución de un ejercicio en una serie. En este proyecto, la repetición se registrará como una unidad de ejecución y no como un valor implícito de esfuerzo.

## Serie

Una serie es un bloque de repeticiones ejecutadas de forma consecutiva con una misma intención de carga o esfuerzo. Se utilizará para registrar el trabajo realizado en una sesión.

## Serie de calentamiento

Una serie de calentamiento es una serie realizada con una carga reducida con el fin de preparar el cuerpo para el trabajo principal. No se considerará equivalente a una serie efectiva a efectos de carga principal.

## Serie efectiva

Una serie efectiva es una serie de trabajo completada y no marcada como calentamiento. El posible umbral de esfuerzo para análisis más avanzados deberá decidirse antes de implementar esa analítica.

## Carga

La carga es la magnitud de esfuerzo que se asigna o se registra en una sesión. En este proyecto se considerará un término amplio y se utilizará junto con el contexto de peso, repeticiones, RIR/RPE y progreso.

## Volumen

El proyecto utilizará inicialmente como medida principal el número de series efectivas completadas. Repeticiones totales y tonelaje serán métricas complementarias, según el análisis que se implemente.

## Tonelaje

El tonelaje es la suma de la carga externa por las repeticiones completadas en las series incluidas. Se utilizará como una métrica complementaria, pero no permite comparar de forma fiable ejercicios muy diferentes y el tratamiento del peso corporal deberá definirse posteriormente.

## Intensidad

La intensidad se distinguirá entre intensidad relativa a la carga y esfuerzo percibido. La primera se relacionará con la carga usada para una tarea concreta; el esfuerzo percibido se expresará mediante RIR o RPE según el contexto.

## Frecuencia

La frecuencia deberá expresarse respecto a un periodo y una unidad concreta, por ejemplo sesiones por semana o exposiciones semanales por grupo muscular. La definición exacta dependerá del análisis que se implemente.

## RIR

RIR significa repetitions in reserve, o repeticiones en reserva. Se utilizará para indicar cuántas repeticiones faltan para llegar al fallo muscular aparente.

## RPE

RPE significa rate of perceived exertion, o escala de esfuerzo percibido. Se utilizará como valor complementario al RIR cuando el usuario o el sistema necesiten registrar una percepción de esfuerzo.

## 1RM

1RM es la mayor carga realmente levantada una vez bajo las condiciones definidas para una ejecución concreta. En este proyecto se utilizará como referencia de rendimiento real, no como una estimación.

## e1RM

e1RM es una estimación de 1RM calculada a partir de una serie submáxima. La fórmula concreta se decidirá antes de implementar esta métrica en el sistema.

## Progresión

La progresión es el cambio favorable en la capacidad de rendimiento, la carga o la adaptación a lo largo del tiempo. Se utilizará como concepto general, no como una métrica única.

## Sobrecarga progresiva

La sobrecarga progresiva es la estrategia de aumentar gradualmente el estímulo de entrenamiento para sostener adaptación. En este proyecto se utilizará como principio de diseño del motor de rutinas y del análisis del progreso.

## Adherencia

La adherencia es la medida de seguimiento de la rutina o del entrenamiento frente al plan esperado. Su fórmula exacta deberá documentar qué sesiones se consideran planificadas, completadas, parciales, reprogramadas o canceladas.

## Rutina

Una rutina es una estructura planificada de entrenamiento que define días, ejercicios, series, repeticiones, cargas objetivo y reglas de progresión. No debe confundirse con una sesión ya realizada.

## Sesión

Una sesión es una instancia concreta de entrenamiento realizada por el usuario. Puede derivar de una rutina, pero conserva su propio historial y no debe alterarse automáticamente por cambios posteriores en la rutina.

## Ejercicio global

Un ejercicio global es un ejercicio compartido y reutilizable en el sistema, no propiedad de un usuario concreto. Se utilizará para el catálogo general del producto.

## Ejercicio personalizado

Un ejercicio personalizado es un ejercicio creado por un usuario concreto para su propio uso o para su contexto. Su propiedad debe vincularse claramente al creador.

## Grupo muscular principal

El grupo muscular principal es el grupo muscular que el ejercicio enfatiza de forma más directa. Se utilizará como etiqueta de dominio en el catálogo de ejercicios.

## Músculos secundarios

Los músculos secundarios son los grupos musculares que colaboran en el ejercicio de forma secundaria. Se utilizarán para describir ejercicio y para análisis parciales.

## Patrón de movimiento

El patrón de movimiento describe la forma general de ejecución del ejercicio, por ejemplo empuje, tracción, sentadilla o giro. Se utilizará para organizar ejercicios y para reglas de generación y equilibrio.

## Medición corporal

Una medición corporal es un registro de variables físicas del usuario, como peso, grasa corporal, cintura, pecho, brazo, cadera o muslo. Se utilizará para seguimiento evolutivo.

## Media móvil

Una media móvil es una agregación temporal que suaviza fluctuaciones en series de datos. Se utilizará como concepto de analítica, pero su implementación concreta deberá documentarse con claridad.

## Objetivo

Un objetivo es una intención de seguimiento o mejora del usuario, como perder grasa, ganar masa muscular o mejorar una capacidad concreta. Puede incluir una fecha o un valor de referencia según la definición final del producto.

## Recomendación

Una recomendación es una propuesta orientada a mejorar el proceso de entrenamiento, seguimiento o interpretación de los datos. Debe ser explícita sobre su base y su nivel de confianza.

## Propuesta

Una propuesta es una acción sugerida por el agente o por el sistema que aún no ha sido aplicada. Se utilizará para separar la idea de la ejecución real.

## Evidencia

La evidencia es la información concreta que respalda una observación, una recomendación o una propuesta. Puede consistir en datos históricos, métricas, contexto del usuario o metadatos de una herramienta del agente.

## Nivel de confianza

El nivel de confianza es una valoración cualitativa o cuantitativa de la solidez de una recomendación o de una inferencia. Debe interpretarse con cautela y no como una garantía de verdad.

## Guardrail

Un guardrail es una barrera o restricción diseñada para limitar comportamientos no deseados del agente o del sistema. Se utilizará para evitar diagnósticos, modificaciones sensibles o decisiones no autorizadas.

## Herramienta del agente

Una herramienta del agente es una capacidad controlada que permite al agente consultar o procesar información del sistema. Debe estar limitada a un conjunto explícito y debe estar documentada.

## Cálculo determinista

Un cálculo determinista es un proceso de transformación de datos que produce un resultado repetible a partir de entradas conocidas. Se utilizará como principio base para las métricas importantes del producto.
