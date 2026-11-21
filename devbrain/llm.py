"""Cliente mínimo de Ollama: embeddings y chat."""
import requests

from . import config


def embed(textos, tipo="documento"):
    # nomic-embed-text rinde mejor con estos prefijos; otros modelos (bge-m3) no los usan.
    if "nomic" in config.EMBED_MODEL:
        prefijo = "search_query: " if tipo == "consulta" else "search_document: "
    else:
        prefijo = ""
    vectores = []
    for i in range(0, len(textos), 16):
        lote = [prefijo + t for t in textos[i:i + 16]]
        r = requests.post(f"{config.OLLAMA_URL}/api/embed",
                          json={"model": config.EMBED_MODEL, "input": lote}, timeout=300)
        r.raise_for_status()
        vectores.extend(r.json()["embeddings"])
    return vectores


def chat(sistema, usuario, num_ctx=None):
    r = requests.post(f"{config.OLLAMA_URL}/api/chat", json={
        "model": config.CHAT_MODEL,
        "stream": False,
        "messages": [{"role": "system", "content": sistema},
                     {"role": "user", "content": usuario}],
        "options": {"temperature": 0, "num_ctx": num_ctx or config.CHAT_CTX},
    }, timeout=600)
    r.raise_for_status()
    return r.json()["message"]["content"].strip()
