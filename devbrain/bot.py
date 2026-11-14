"""Bot de Slack @DevBrain (Socket Mode: no necesita URL pública).

Ejecutar desde la raíz del repositorio:  python -m devbrain.bot
"""
import logging
import re
import threading
import time

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from . import answer, config, github_pr, ingest, postmortem

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("devbrain")
_trabajo = threading.Lock()  # el modelo local atiende una petición a la vez

app = App(token=config.requerido("SLACK_BOT_TOKEN"))


def generar_y_publicar(client, canal):
    ruta, titulo, contenido = postmortem.generar(client, canal)
    nombre = client.conversations_info(channel=canal)["channel"]["name"]
    return github_pr.abrir_pr(ruta, titulo, contenido, nombre), ruta


@app.event("app_mention")
def mencion(event, say, client):
    texto = re.sub(r"<@\w+>", "", event.get("text", "")).strip()
    hilo = event.get("thread_ts") or event["ts"]
    if not texto:
        say(text="Pregúntame algo de la bóveda, o escribe `@DevBrain postmortem` en un canal de incidente.",
            thread_ts=hilo)
        return

    if re.search(r"post[\s-]?mortem", texto, re.I):
        say(text="Leyendo el canal y redactando el post-mortem. Puede tardar unos minutos…", thread_ts=hilo)
        try:
            with _trabajo:
                url, ruta = generar_y_publicar(client, event["channel"])
            say(text=f"Abrí el Pull Request con el borrador `{ruta}`:\n{url}\n"
                     "Revísalo contra el historial antes de aprobarlo.", thread_ts=hilo)
        except Exception as e:
            log.exception("Error generando post-mortem")
            say(text=f"No pude generar el post-mortem: {e}", thread_ts=hilo)
        return

    say(text="🔎 Buscando en la bóveda…", thread_ts=hilo)
    try:
        with _trabajo:
            respuesta = answer.responder(texto)
    except Exception as e:
        log.exception("Error respondiendo")
        respuesta = (f"No pude consultar la bóveda ({e}). Revisa que Ollama esté encendido. "
                     "Si es una caída activa, escala por PagerDuty.")
    say(text=respuesta, thread_ts=hilo, unfurl_links=False)


def _al_archivar(event, client):
    canal = event["channel"]
    try:
        nombre = client.conversations_info(channel=canal)["channel"]["name"]
    except Exception:
        log.exception("No pude leer el canal archivado")
        return
    if not nombre.startswith(config.INCIDENT_PREFIX):
        return
    try:
        with _trabajo:
            url, ruta = generar_y_publicar(client, canal)
        mensaje = f"Post-mortem de #{nombre} listo para revisión: {url}"
    except Exception as e:
        log.exception("Error en post-mortem automático")
        mensaje = (f"No pude generar el post-mortem de #{nombre} ({e}). "
                   "Desarchiva el canal y usa `@DevBrain postmortem` antes de cerrarlo.")
    if config.NOTIFY_CHANNEL:
        client.chat_postMessage(channel=config.NOTIFY_CHANNEL, text=mensaje)
    else:
        log.info(mensaje)


@app.event("channel_archive")
def canal_archivado(event, client):
    _al_archivar(event, client)


@app.event("group_archive")
def grupo_archivado(event, client):
    _al_archivar(event, client)


def sincronizacion_periodica():
    while True:
        time.sleep(config.SYNC_MINUTES * 60)
        try:
            if ingest.sincronizar() or ingest.necesita_indexar():
                with _trabajo:
                    ingest.indexar()
        except Exception:
            log.exception("Falló la sincronización con la rama principal")


def main():
    log.info("Bóveda: %s", config.VAULT_PATH)
    ingest.sincronizar()
    if ingest.necesita_indexar():
        log.info("Indexando la bóveda…")
        ingest.indexar()
    threading.Thread(target=sincronizacion_periodica, daemon=True).start()
    log.info("DevBrain conectado. Revisando %s cada %d min.", config.GIT_BRANCH, config.SYNC_MINUTES)
    SocketModeHandler(app, config.requerido("SLACK_APP_TOKEN")).start()


if __name__ == "__main__":
    main()
