"""Base vectorial Qdrant en modo local.

Cada reindexación crea una colección nueva y solo cambia el puntero al terminar,
así el bot sigue respondiendo con el índice anterior mientras se reconstruye.
Qdrant local solo admite un proceso a la vez: no ejecutes ingest.py con el bot encendido.
"""
import atexit
import json
import threading
import time

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from . import config

_lock = threading.Lock()
_cliente = None


def cliente():
    global _cliente
    if _cliente is None:
        config.QDRANT_PATH.mkdir(parents=True, exist_ok=True)
        _cliente = QdrantClient(path=str(config.QDRANT_PATH))
        atexit.register(_cliente.close)
    return _cliente


def estado():
    try:
        return json.loads(config.STATE_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return {}


def reconstruir(fragmentos, vectores, commit):
    nombre = f"devcore_{int(time.time())}"
    c = cliente()
    c.create_collection(nombre, vectors_config=VectorParams(size=len(vectores[0]), distance=Distance.COSINE))
    c.upsert(nombre, points=[
        PointStruct(id=f["id"], vector=v, payload=f) for f, v in zip(fragmentos, vectores)
    ])
    with _lock:
        anterior = estado().get("coleccion")
        config.STATE_FILE.write_text(json.dumps({
            "coleccion": nombre, "commit": commit, "fragmentos": len(fragmentos),
            "actualizado": time.strftime("%Y-%m-%d %H:%M:%S"),
        }, indent=2), encoding="utf-8")
    if anterior and anterior != nombre and c.collection_exists(anterior):
        c.delete_collection(anterior)


def buscar(vector, k):
    coleccion = estado().get("coleccion")
    if not coleccion:
        return []
    resultado = cliente().query_points(coleccion, query=vector, limit=k, with_payload=True)
    return [(p.score, p.payload) for p in resultado.points]
