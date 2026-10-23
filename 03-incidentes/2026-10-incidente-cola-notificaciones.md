---
tipo: postmortem
id: PM-2026-10-01
titulo: Corrupción de la cola de notificaciones
estado: borrador
fecha_creacion: 2026-10-22
ultima_revision: 2026-10-22
responsable: por definir
servicios: [notificaciones]
etiquetas: [incidente, base-de-datos, runbook, severidad-critica]
relacionados: ["[[MOC-Incidentes]]", "[[runbook-notificaciones]]", "[[indice-errores-recurrentes]]", "[[ADR-0002-runbooks-en-el-repositorio]]"]
---

# Post-mortem: corrupción de la cola de notificaciones

- **Inicio:** martes, 03:00 AM
- **Duración (MTTR):** 4.5 horas
- **Impacto:** servicio de notificaciones caído, base de datos de cola corrupta, pérdida estimada de USD 120.000 y pérdida de confianza de 3 clientes enterprise.
- **Severidad:** crítica

## Resumen

El servicio de notificaciones colapsó de madrugada. El ingeniero de guardia, con dos meses en la empresa, no encontró un runbook actualizado. Aplicó una solución de un ticket de Jira de 2022, que corrompió la base de datos de la cola de mensajes.

## Causa raíz

- El runbook vigente no era accesible durante el incidente.
- La documentación estaba separada del código y no se mantenía.
- No había un paso que obligara a verificar la versión de una solución antes de aplicarla.

## Acciones correctivas

| Acción | Responsable | Fecha límite | Ticket |
|---|---|---|---|
| Mover el runbook a `04-servicios/notificaciones/` | por definir | por definir | por definir |
| Agregar validación de runbook en CI | por definir | por definir | por definir |
| Registrar el caso en el índice de errores recurrentes | por definir | por definir | por definir |

## Conocimiento a registrar

- Runbook: [[runbook-notificaciones]]
- Índice: [[indice-errores-recurrentes]]
- Decisión: [[ADR-0002-runbooks-en-el-repositorio]]
