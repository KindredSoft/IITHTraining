import json
import time
import urllib.error
import urllib.request

from config import GEMINI_API_KEY, LLM_PROVIDER, MODEL_NAME, OLLAMA_URL


def _ollama(prompt: str, json_mode: bool = False) -> str:
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
    }
    if json_mode:
        payload["format"] = "json"

    request = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            body = json.loads(response.read().decode("utf-8"))
            return str(body.get("response", ""))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return ""


def _gemini(prompt: str, json_mode: bool = False) -> str:
    if not GEMINI_API_KEY:
        return ""
    try:
        from google import genai
    except ImportError:
        return ""

    client = genai.Client(api_key=GEMINI_API_KEY)
    config = {"response_mime_type": "application/json"} if json_mode else {}

    for attempt in range(4):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=config,
            )
            return response.text or ""
        except Exception as exc:
            message = str(exc).lower()
            retryable = any(token in message for token in ("429", "503", "quota", "resource_exhausted"))
            if not retryable or attempt == 3:
                return ""
            time.sleep(2 ** attempt)
    return ""


def generate_text(prompt: str, json_mode: bool = False) -> str:
    if LLM_PROVIDER == "gemini":
        return _gemini(prompt, json_mode)
    return _ollama(prompt, json_mode)


def generate_object(prompt: str) -> dict:
    raw = generate_text(prompt, json_mode=True)
    try:
        value = json.loads(raw)
        return value if isinstance(value, dict) else {}
    except json.JSONDecodeError:
        return {}
