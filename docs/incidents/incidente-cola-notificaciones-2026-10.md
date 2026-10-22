# Post-mortem: corrupción de la cola de notificaciones

- **Fecha y hora de inicio:** martes, 03:00 AM
- **Duración (MTTR):** 4.5 horas
- **Impacto:** servicio de notificaciones caído, base de datos de cola corrupta, pérdida estimada de USD 120.000 y pérdida de confianza de 3 clientes enterprise
- **Severidad:** crítica
- **Etiquetas:** #notificaciones #base-de-datos #runbook

## Resumen

El servicio de notificaciones colapsó de madrugada. El ingeniero de guardia, con dos meses en la empresa, no encontró un runbook actualizado. Aplicó una solución de un ticket de Jira de 2022, que corrompió la base de datos de la cola de mensajes.

## Causa raíz

- El runbook vigente no existía en un lugar accesible durante el incidente.
- La documentación estaba en Confluence, separada del código, y no se mantenía.
- No había un proceso que obligara a revisar la versión de una solución antes de aplicarla.

## Acciones correctivas

| Acción | Responsable | Fecha límite | Enlace a ticket |
|---|---|---|---|
| Mover el runbook de notificaciones a `services/notificaciones/runbook.md` | | | |
| Agregar validación de runbook en CI | | | |
| Registrar este caso en el índice de errores recurrentes | | | |

## Conocimiento a registrar

- Runbook: [[notificaciones-runbook]]
- Entrada en el [[indice-errores-recurrentes]]
