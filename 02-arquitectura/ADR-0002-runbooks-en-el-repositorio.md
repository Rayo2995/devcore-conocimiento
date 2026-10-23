---
tipo: adr
id: ADR-0002
titulo: Mantener los runbooks en el mismo repositorio que el código
estado: propuesta
fecha_creacion: 2026-10-22
ultima_revision: 2026-10-22
responsable: por definir
servicios: [notificaciones, facturacion-legacy]
etiquetas: [arquitectura, runbooks, ci-cd]
relacionados: ["[[MOC-Arquitectura]]", "[[runbook-notificaciones]]", "[[2026-10-incidente-cola-notificaciones]]"]
---

# ADR-0002: Mantener los runbooks en el mismo repositorio que el código

## Contexto

El runbook de despliegue estaba en Confluence y quedó obsoleto. Un paso omitido en ese documento fue la causa de un incidente grave. El runbook no se actualizaba cuando cambiaba el código.

## Opciones consideradas

1. Mantener los runbooks en Confluence con revisión manual: ya demostró que no funciona.
2. Runbooks en el repositorio del servicio, con validación en CI: el cambio de código y el del runbook se revisan en el mismo PR.

## Decisión

Propuesta: cada servicio guarda su runbook en `04-servicios/<servicio>/runbook-<servicio>.md`. El pipeline de CI falla si un PR modifica `src/` sin modificar el runbook.

## Consecuencias

- Los runbooks se revisan junto con el código.
- Aumenta el costo de cada PR que cambia comportamiento.
- Queda pendiente definir cómo se valida que un runbook sea ejecutable, por ejemplo en staging.
