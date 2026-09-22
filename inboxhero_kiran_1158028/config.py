from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RUNTIME_DIR = BASE_DIR / "runtime"
OUTBOX_DIR = BASE_DIR / "outbox"

INBOX_PATH = DATA_DIR / "inbox.json"
PREFERENCES_PATH = DATA_DIR / "preferences.json"
DECISIONS_PATH = RUNTIME_DIR / "decisions.json"
TRACE_PATH = RUNTIME_DIR / "trace.jsonl"

LLM_PROVIDER = os.getenv("INBOXHERO_LLM", "ollama").lower()
MODEL_NAME = os.getenv("INBOXHERO_MODEL", "phi3")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

for directory in (DATA_DIR, RUNTIME_DIR, OUTBOX_DIR):
    directory.mkdir(parents=True, exist_ok=True)
