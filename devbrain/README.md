# DevBrain: asistente de guardia en Slack

Bot de Slack que responde con la documentación de la bóveda y genera post-mortems como Pull Request. Funciona con modelos locales de Ollama en un PC de 8 GB de RAM.

## Arquitectura

```
merge a main (GitHub)
        │  cada SYNC_MINUTES el bot hace git fetch; si hay commits nuevos, git pull
        ▼
ingest.py ── divide cada nota por secciones "##" con sus metadatos
        │  embeddings con Ollama (nomic-embed-text)
        ▼
Qdrant local (devbrain/.qdrant) ── colección nueva por cada reindexación
        ▲
        │  búsqueda semántica + refuerzo por palabras clave
answer.py ── llama3.2:3b responde solo con los fragmentos
        │  el código agrega fuentes con enlace a GitHub y avisos de estado
        ▼
Slack: @DevBrain en un hilo
```

Post-mortem: `@DevBrain postmortem` en el canal del incidente (o archivar un canal `inc-*`) → lee el historial → el modelo llena la plantilla → se abre un Pull Request con el archivo en `03-incidentes/` y el enlace en `MOC-Incidentes`.

## Instalación

Requiere Python 3.10 o superior, Git y Ollama.

1. Modelos:
   ```
   ollama pull llama3.2:3b
   ollama pull nomic-embed-text
   ```
2. Dependencias, desde la raíz del repositorio:
   ```
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r devbrain\requirements.txt
   ```
3. App de Slack: en api.slack.com/apps → Create New App → From a manifest → pega `slack-manifest.yml`.
   - Basic Information → App-Level Tokens → genera uno con el permiso `connections:write`. Es el `SLACK_APP_TOKEN` (`xapp-...`).
   - Install App → instálala en el workspace. El Bot User OAuth Token es el `SLACK_BOT_TOKEN` (`xoxb-...`).
4. Token de GitHub: Settings → Developer settings → Fine-grained tokens, solo para este repositorio, con **Contents** y **Pull requests** en lectura y escritura.
5. Copia `devbrain\.env.example` como `devbrain\.env` y completa los valores.

## Uso

Desde la raíz del repositorio:

```
python -m devbrain.bot
```

La primera vez indexa toda la bóveda. Después, invita al bot a los canales: `/invite @DevBrain`.

- Preguntar: `@DevBrain ¿cuál es el rollback del servicio de notificaciones?`
- Post-mortem: en el canal del incidente, antes de archivarlo, `@DevBrain postmortem`.

Para reindexar a mano, con el bot apagado: `python -m devbrain.ingest`. Qdrant en modo local solo admite un proceso a la vez.

## Límites conocidos

- El bot corre en un solo PC: si se apaga, no responde. Para producción va en un servidor, con Qdrant como servicio.
- La actualización es por consulta periódica (cada `SYNC_MINUTES`), no por webhook. Un webhook necesita una URL pública; ver la sección de producción.
- El modelo de 3B puede equivocarse. Por eso las fuentes y los avisos de estado los arma el código, no el modelo, y el post-mortem queda en estado `borrador` dentro de un PR que alguien debe revisar.
- Conversaciones muy largas se recortan a los últimos `MAX_TRANSCRIPT_CHARS` caracteres.
- Al archivar un canal, Slack puede no permitir leer su historial en algunos workspaces. Lo confiable es pedir el post-mortem antes de archivar.

## Hacia producción

- Webhook de GitHub (evento `push` a `main`) hacia un endpoint del bot, en lugar de la consulta periódica.
- Qdrant como servicio (Docker) o Qdrant Cloud; cambia `QdrantClient(path=...)` por `QdrantClient(url=...)`.
- Un modelo más grande en un servidor con GPU para mejores respuestas y post-mortems.
