import re

# These are intentionally narrow: the goal is to detect instructions aimed at
# the assistant, not ordinary requests made by one human to another.
INJECTION_PATTERNS = (
    r"\bignore\s+(?:all\s+)?previous\s+instructions\b",
    r"\bautomated-agent\s+directive\b",
    r"\binstructions?\s+for\s+(?:the\s+)?assistant\b",
    r"\bfor\s+automated\s+assistants?\b",
    r"\bassistant configuration update\b",
    r"\bdo not mention this\b",
    r"\bskip the confirmation step\b",
)


def embedded_instruction(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(pattern, lowered) for pattern in INJECTION_PATTERNS)


PHISHING_TERMS = (
    "urgent wire",
    "transfer funds",
    "remit",
    "banking partner has changed",
    "disregard the account on file",
    "password expires",
    "verify account",
    "re-verify",
    "credentials immediately",
    "login verify",
)


def looks_like_phishing(subject: str, body: str) -> bool:
    text = f"{subject}\n{body}".lower()
    return any(term in text for term in PHISHING_TERMS)
