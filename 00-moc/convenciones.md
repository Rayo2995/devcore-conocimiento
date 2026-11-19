---
tipo: guia
id: GUI-001
titulo: Convenciones del repositorio
estado: vigente
fecha_creacion: 2026-10-22
ultima_revision: 2026-10-22
responsable: por definir
servicios: [todos]
etiquetas: [convenciones, metadatos]
relacionados: ["[[00-MOC-DevCore]]", "[[como-usar-los-MOC]]"]
---

# Convenciones del repositorio

## Nombres de archivo

- Minúsculas, sin tildes, separadas por guiones: `servicio-notificaciones.md`.
- ADR: `ADR-NNNN-titulo-corto.md`, con número consecutivo.
- Post-mortem: `AAAA-MM-incidente-slug.md`.
- Formato: `codigo-en-minusculas-titulo-corto.md`, por ejemplo `gad-ft-003-acta-informe-de-siniestro.md`. Los procedimientos siguen la misma regla (`gco-pr-002-licitacion-publica.md`). El archivo original (Word, Excel, PDF) va en la subcarpeta `archivos/` del proceso, con su nombre oficial.
- Cada nombre de archivo es único en todo el vault, para que los enlaces `[[nombre]]` no sean ambiguos.

## Metadatos obligatorios

Todo documento empieza con un bloque YAML entre `---`. Campos:

| Campo | Descripción |
|---|---|
| `tipo` | `moc`, `guia`, `adr`, `postmortem`, `indice`, `servicio`, `runbook`, `transferencia`, `formato`, `procedimiento` |
| `id` | Identificador corto, por ejemplo `ADR-0001` |
| `titulo` | Título legible |
| `estado` | `borrador`, `propuesta`, `aceptada`, `vigente`, `reemplazada` |
| `fecha_creacion` | `AAAA-MM-DD` |
| `ultima_revision` | `AAAA-MM-DD`, se actualiza al cambiar el contenido |
| `responsable` | Persona o equipo responsable |
| `servicios` | Lista de servicios afectados, o `[todos]` |
| `etiquetas` | Lista de etiquetas en minúsculas |
| `relacionados` | Lista de enlaces a otros documentos |

## Enlaces

- Usar enlaces `[[nombre]]` en lugar de rutas.
- Todo documento debe estar enlazado desde al menos un MOC.

## Revisión

- Un runbook se revisa cada vez que cambia el código de su servicio, y como mínimo cada trimestre.
- Un ADR aceptado no se edita; si cambia la decisión, se crea uno nuevo que lo reemplaza.
