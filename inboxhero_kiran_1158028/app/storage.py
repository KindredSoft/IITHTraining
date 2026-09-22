import json
from pathlib import Path
from typing import Any, Iterable

from config import DECISIONS_PATH, INBOX_PATH, PREFERENCES_PATH, TRACE_PATH


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def load_messages():
    from app.models import Message

    raw = _read_json(INBOX_PATH, [])
    if not isinstance(raw, list):
        raise ValueError("inbox.json must contain a JSON array")
    return [Message.from_dict(item) for item in raw]


def load_preferences() -> dict[str, Any]:
    value = _read_json(PREFERENCES_PATH, {})
    return value if isinstance(value, dict) else {}


def save_preferences(values: dict[str, Any]) -> None:
    PREFERENCES_PATH.write_text(
        json.dumps(values, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def load_decisions() -> dict[str, Any]:
    value = _read_json(DECISIONS_PATH, {})
    return value if isinstance(value, dict) else {}


def save_decisions(values: dict[str, Any]) -> None:
    DECISIONS_PATH.write_text(
        json.dumps(values, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def append_event(capability: str, event: str, details: dict[str, Any]) -> None:
    record = {"cap": capability, "event": event, "details": details}
    with TRACE_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def read_events() -> Iterable[dict[str, Any]]:
    if not TRACE_PATH.exists():
        return []
    events = []
    for line in TRACE_PATH.read_text(encoding="utf-8").splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events
