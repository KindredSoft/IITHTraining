from app.storage import load_preferences, save_preferences


def set_preference(key: str, value: str) -> None:
    prefs = load_preferences()
    prefs[key] = value
    save_preferences(prefs)


def format_preferences() -> str:
    prefs = load_preferences()
    if not prefs:
        return "None"
    return "\n".join(f"- {key}: {value}" for key, value in prefs.items())
