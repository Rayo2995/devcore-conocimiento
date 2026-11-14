"""Configuración de DevBrain. Todo se lee de devbrain/.env (ver .env.example)."""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).with_name(".env"))
except ImportError:
    pass

BASE = Path(__file__).resolve().parent


def _get(nombre, defecto=None):
    valor = os.getenv(nombre, defecto)
    return valor.strip() if isinstance(valor, str) else valor


def requerido(nombre):
    valor = _get(nombre)
    if not valor:
        raise SystemExit(f"Falta la variable {nombre} en devbrain/.env")
    return valor


# Bóveda (repositorio de documentación)
VAULT_PATH = Path(_get("VAULT_PATH", str(BASE.parent))).resolve()
GIT_BRANCH = _get("GIT_BRANCH", "main")
SYNC_MINUTES = int(_get("SYNC_MINUTES", "5"))

# GitHub
GITHUB_REPO = _get("GITHUB_REPO", "Rayo2995/devcore-conocimiento")
GITHUB_TOKEN = _get("GITHUB_TOKEN")
INCIDENTS_DIR = _get("INCIDENTS_DIR", "03-incidentes")
INCIDENTS_MOC = _get("INCIDENTS_MOC", "00-moc/MOC-Incidentes.md")

# Ollama
OLLAMA_URL = _get("OLLAMA_URL", "http://localhost:11434").rstrip("/")
CHAT_MODEL = _get("CHAT_MODEL", "llama3.2:3b")
EMBED_MODEL = _get("EMBED_MODEL", "nomic-embed-text")
CHAT_CTX = int(_get("CHAT_CTX", "4096"))
POSTMORTEM_CTX = int(_get("POSTMORTEM_CTX", "8192"))

# Base vectorial (Qdrant en modo local: un archivo en disco, sin servidor)
QDRANT_PATH = Path(_get("QDRANT_PATH", str(BASE / ".qdrant"))).resolve()
STATE_FILE = BASE / ".qdrant" / "estado.json"
TOP_K = int(_get("TOP_K", "4"))
MIN_SCORE = float(_get("MIN_SCORE", "0.35"))

# Slack
SLACK_BOT_TOKEN = _get("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = _get("SLACK_APP_TOKEN")
INCIDENT_PREFIX = _get("INCIDENT_PREFIX", "inc-")
NOTIFY_CHANNEL = _get("NOTIFY_CHANNEL")
TIMEZONE = _get("TIMEZONE", "America/Bogota")
MAX_TRANSCRIPT_CHARS = int(_get("MAX_TRANSCRIPT_CHARS", "12000"))
