---
tipo: runbook
id: RB-001
titulo: Runbook del servicio de notificaciones
estado: borrador
fecha_creacion: 2026-10-22
ultima_revision: 2026-10-22
responsable: por definir
servicios: [notificaciones]
etiquetas: [runbook, cola-de-mensajes, rollback]
relacionados: ["[[MOC-Servicios]]", "[[servicio-notificaciones]]", "[[indice-errores-recurrentes]]"]
---

# Runbook del servicio de notificaciones

**Estado:** borrador. Pendiente de validar en staging antes de usarse en producción.

## Diagnóstico rápido

1. Revisar el estado del servicio en el panel de monitoreo.
2. Revisar la profundidad de la cola de mensajes.
3. Si la cola no responde, no reiniciar ni restaurar sin revisar la sección de restauración.

## Restauración de la cola

Pendiente de documentar. No aplicar soluciones de tickets antiguos sin verificar la versión del sistema. Ver [[indice-errores-recurrentes]].

## Rollback de despliegue

1. Identificar la última versión estable con la etiqueta de release.
2. Desplegar esa versión con el pipeline de rollback.
3. Verificar que la cola procesa mensajes.

## Escalamiento

Si el incidente supera 30 minutos, escalar al responsable del servicio mediante PagerDuty.
