---
tipo: adr
id: ADR-003
titulo: '"No usar Redis en el servicio de logística (ejemplo de prueba)"'
estado: aceptada
fecha_creacion: 2026-11-07
ultima_revision: 2026-11-07
responsable: por definir
servicios:
  - logistica
etiquetas:
  - arquitectura
  - prueba
relacionados:
  - "[[MOC-Arquitectura]]"
---


# ADR-0003: No usar Redis en el servicio de logística (ejemplo de prueba)

## Contexto
El servicio de logística necesita una cola de eventos con garantía de orden por entrega.
## Opciones consideradas
1. Redis con listas: baja latencia, pero sin persistencia fuerte ni retención de eventos. 
2. Otra opción de mensajería con log persistente.
## Decisión
No usar Redis en logística, porque los eventos deben conservarse para auditoría y reprocesamiento.
## Consecuencias
Hay que operar una infraestructura de mensajería con log persistente, lo que aumenta la complejidad.