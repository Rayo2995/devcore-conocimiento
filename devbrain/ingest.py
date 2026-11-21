"""Ingesta: sincroniza la rama principal y reconstruye el índice vectorial.

Uso manual (con el bot apagado):  python -m devbrain.ingest
"""
import logging
import subprocess

from . import config, llm, store, vault

log = logging.getLogger("devbrain.ingest")


def _git(*args):
    return subprocess.run(["git", "-C", str(config.VAULT_PATH), *args],
                          capture_output=True, text=True, check=True).stdout.strip()


# Cambia este número cuando cambie la forma de leer o fragmentar las notas:
# el bot reconstruye el índice solo al arrancar.
VERSION_INDICE = "3"


def commit_actual():
    try:
        return f"{_git('rev-parse', 'HEAD')}:{VERSION_INDICE}"
    except (subprocess.CalledProcessError, FileNotFoundError):
        return f"sin-git:{VERSION_INDICE}"


def sincronizar():
    """Trae los merges nuevos de la rama principal. Devuelve True si cambió algo."""
    try:
        _git("fetch", "origin", config.GIT_BRANCH)
        local, remoto = _git("rev-parse", "HEAD"), _git("rev-parse", f"origin/{config.GIT_BRANCH}")
        if local == remoto:
            return False
        _git("pull", "--ff-only", "origin", config.GIT_BRANCH)
        log.info("Nuevos cambios en %s: %s -> %s", config.GIT_BRANCH, local[:7], remoto[:7])
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        log.warning("No se pudo sincronizar con GitHub: %s", getattr(e, "stderr", e))
        return False


def indexar():
    docs = vault.leer_documentos(config.VAULT_PATH)
    fragmentos = [f for d in docs for f in vault.fragmentar(d)]
    if not fragmentos:
        raise SystemExit(f"No hay notas para indexar en {config.VAULT_PATH}")
    vectores = llm.embed([f["texto"] for f in fragmentos], "documento")
    store.reconstruir(fragmentos, vectores, commit_actual())
    log.info("Índice listo: %d documentos, %d fragmentos", len(docs), len(fragmentos))
    return len(docs), len(fragmentos)


def necesita_indexar():
    return store.estado().get("commit") != commit_actual()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    sincronizar()
    d, f = indexar()
    print(f"Indexados {d} documentos en {f} fragmentos.")
