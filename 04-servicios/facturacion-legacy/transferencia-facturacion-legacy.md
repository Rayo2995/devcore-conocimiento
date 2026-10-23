---
tipo: transferencia
id: TRF-001
titulo: Plan de transferencia de conocimiento de facturación legacy
estado: propuesta
fecha_creacion: 2026-10-22
ultima_revision: 2026-10-22
responsable: por definir
servicios: [facturacion-legacy]
etiquetas: [transferencia, bus-factor, urgente]
relacionados: ["[[MOC-Servicios]]", "[[servicio-facturacion-legacy]]", "[[runbook-facturacion-legacy]]"]
---

# Plan de transferencia de conocimiento

**Meta:** bus factor de al menos 2 antes de la salida del responsable actual.

## Sesiones

1. Recorrido del módulo: arquitectura general y puntos de entrada.
2. Mapa de dependencias: qué servicios llaman a facturación.
3. Procedimientos de operación: despliegue, rollback y fallos conocidos.
4. Pair programming: un ingeniero hace un cambio real con acompañamiento.
5. Revisión: el segundo ingeniero documenta lo que entendió y el responsable corrige.

## Entregables

- [ ] Mapa de dependencias completo en [[servicio-facturacion-legacy]]
- [ ] Runbook de despliegue y rollback: [[runbook-facturacion-legacy]]
- [ ] ADR de las decisiones históricas que aún importan
- [ ] Notas de cada sesión, enlazadas desde este documento
