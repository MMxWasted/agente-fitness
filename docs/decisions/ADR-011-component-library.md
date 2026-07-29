# ADR-011 — Biblioteca de componentes de interfaz

- Identificador: `ADR-011`
- Estado: `Proposed`

## Contexto

La interfaz prevista será React con TypeScript y mobile-first, pero aún no existe frontend ni una biblioteca seleccionada. La decisión influirá en accesibilidad, consistencia, personalización, tamaño del cliente y velocidad de desarrollo.

## Fuerzas o criterios de decisión

- Accesibilidad por defecto y capacidad de validarla.
- Experiencia mobile-first.
- Personalización visual y coherencia.
- Coste de mantenimiento.
- Tamaño y rendimiento.
- Velocidad de desarrollo.
- Compatibilidad y madurez en React.

## Decisión propuesta

No se selecciona todavía una biblioteca ni un enfoque definitivo. Antes de iniciar componentes compartidos se evaluarán alternativas con un conjunto pequeño de casos representativos: formularios, navegación móvil, diálogos de confirmación, estados de carga/error y visualización accesible de métricas.

## Alternativas consideradas

- **Componentes propios:** máximo control y menor dependencia, con mayor coste de accesibilidad y mantenimiento.
- **Biblioteca accesible sin estilos cerrados:** aporta primitivas y comportamiento, pero exige construir el sistema visual.
- **Biblioteca completa de interfaz:** acelera pantallas y consistencia, a cambio de mayor peso y restricciones de personalización.
- **Enfoque híbrido:** combina primitivas externas y componentes propios; puede equilibrar necesidades, pero requiere reglas para evitar duplicidad.

## Consecuencias positivas

- La selección se basará en casos reales y criterios explícitos.
- Se evita añadir una dependencia antes de necesitarla.
- Accesibilidad y mobile-first quedan como requisitos de evaluación.

## Consecuencias negativas

- El sistema visual y los componentes base siguen pendientes.
- Será necesario realizar una evaluación antes de construir pantallas.
- Cambiar tarde de alternativa podría resultar costoso.

## Riesgos

- Elegir por popularidad sin validar accesibilidad.
- Incorporar una dependencia grande para pocos componentes.
- Crear componentes propios inconsistentes o difíciles de mantener.
- Mezclar bibliotecas con patrones superpuestos.

## Impacto en seguridad y privacidad

Los componentes no deben almacenar secretos ni sustituir validación backend. Formularios y confirmaciones deberán evitar exposición accidental de datos, comunicar acciones sensibles con claridad y conservar accesibilidad. Las dependencias elegidas requerirán revisión de mantenimiento, seguridad y licencia.

## Condiciones de revisión

La propuesta deberá resolverse antes de establecer el sistema de componentes compartidos. Se revisará si cambian los requisitos de accesibilidad, React, rendimiento, identidad visual o soporte móvil.

## Documentos relacionados

- [Visión de producto](../product/vision.md)
- [Arquitectura general](../architecture/overview.md)
- [Convenciones](../CONVENCIONES.md)

