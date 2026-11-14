"""Lectura de la bóveda: separa metadatos YAML y divide cada nota por secciones."""
import re
import uuid
from pathlib import Path

EXCLUIDAS = {".obsidian", ".github", ".git", ".trash", "adjuntos", "05-plantillas",
             "devbrain", "scripts", "src"}
MAX_CHUNK = 1500


def parse_frontmatter(texto):
    texto = texto.replace("\r\n", "\n")
    meta = {}
    if not texto.startswith("---\n"):
        return meta, texto
    fin = texto.find("\n---", 4)
    if fin == -1:
        return meta, texto
    for linea in texto[4:fin].splitlines():
        if ":" not in linea or linea.startswith((" ", "-")):
            continue
        clave, valor = linea.split(":", 1)
        valor = valor.strip()
        if valor.startswith("[") and valor.endswith("]"):
            valor = [v.strip().strip('"').strip("'") for v in valor[1:-1].split(",") if v.strip()]
        else:
            valor = valor.strip('"').strip("'")
        meta[clave.strip()] = valor
    return meta, texto[fin + 4:].lstrip("\n")


def _partir(texto, limite=MAX_CHUNK):
    if len(texto) <= limite:
        return [texto]
    partes, actual = [], ""
    for parrafo in texto.split("\n\n"):
        if actual and len(actual) + len(parrafo) + 2 > limite:
            partes.append(actual)
            actual = parrafo
        else:
            actual = f"{actual}\n\n{parrafo}" if actual else parrafo
    if actual:
        partes.append(actual)
    return partes


def leer_documentos(vault: Path):
    docs = []
    for ruta in sorted(vault.rglob("*.md")):
        rel = ruta.relative_to(vault)
        if any(p in EXCLUIDAS for p in rel.parts):
            continue
        meta, cuerpo = parse_frontmatter(ruta.read_text(encoding="utf-8", errors="ignore"))
        docs.append({"ruta": rel.as_posix(), "meta": meta, "cuerpo": cuerpo})
    return docs


def fragmentar(doc):
    """Un fragmento por sección '## '. Cada fragmento conserva título, id, estado y ruta."""
    meta = doc["meta"]
    titulo = meta.get("titulo") or Path(doc["ruta"]).stem
    secciones = re.split(r"(?m)^(?=## )", doc["cuerpo"])
    fragmentos = []
    for i, seccion in enumerate(s for s in secciones if s.strip()):
        encabezado = seccion.splitlines()[0].lstrip("#").strip() if seccion.startswith("## ") else "Introducción"
        for j, parte in enumerate(_partir(seccion.strip())):
            fragmentos.append({
                "id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"{doc['ruta']}#{i}.{j}")),
                "ruta": doc["ruta"],
                "doc_id": meta.get("id", ""),
                "titulo": titulo,
                "tipo": meta.get("tipo", ""),
                "estado": meta.get("estado", ""),
                "seccion": encabezado,
                "texto": f"{titulo} — {encabezado}\n\n{parte}",
            })
    return fragmentos
