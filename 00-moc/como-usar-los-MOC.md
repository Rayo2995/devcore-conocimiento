---
tipo: guia
id: GUI-002
titulo: Cómo usar los MOC
estado: vigente
fecha_creacion: 2026-10-22
ultima_revision: 2026-10-22
responsable: por definir
servicios: [todos]
etiquetas: [moc, guia]
relacionados: ["[[00-MOC-DevCore]]", "[[convenciones]]"]
---

# Cómo usar los MOC

Un MOC (Map of Content) es una nota que organiza enlaces a otras notas por tema. No contiene el conocimiento en sí; sirve para orientarse.

## Estructura

- Hay un único MOC raíz: [[00-MOC-DevCore]].
- Cada área tiene su propio MOC: onboarding, arquitectura, incidentes y servicios.
- Un MOC solo enlaza a documentos de su área. Si un documento pertenece a dos áreas, se enlaza desde ambas.

## Reglas

1. Cuando se crea un documento, se agrega al MOC de su área en el mismo Pull Request.
2. Un MOC incluye una sección "Por crear" con los documentos pendientes. Cuando se escriben, se mueven a "Documentos".
3. Los MOC se revisan al menos una vez al trimestre para eliminar enlaces rotos.

## Cómo crear un MOC nuevo

1. En Obsidian, crea una nota en `00-moc/`.
2. Insértala con la plantilla `moc`.
3. Enlázala desde [[00-MOC-DevCore]].
