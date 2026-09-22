from dataclasses import dataclass
from typing import Any


DISPOSITIONS = {"reply", "archive", "defer", "delegate", "escalate"}


@dataclass(frozen=True)
class Message:
    id: str
    thread_id: str
    sender: str
    recipient: str
    subject: str
    timestamp: str
    unread: bool
    body: str

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Message":
        required = ("id", "thread_id", "from", "to", "subject", "timestamp", "unread", "body")
        missing = [key for key in required if key not in raw]
        if missing:
            raise ValueError(f"Message is missing fields: {', '.join(missing)}")

        return cls(
            id=str(raw["id"]),
            thread_id=str(raw["thread_id"]),
            sender=str(raw["from"]),
            recipient=str(raw["to"]),
            subject=str(raw["subject"]),
            timestamp=str(raw["timestamp"]),
            unread=bool(raw["unread"]),
            body=str(raw["body"]),
        )

    def as_prompt_text(self) -> str:
        return (
            f"Message ID: {self.id}\n"
            f"From: {self.sender}\n"
            f"To: {self.recipient}\n"
            f"Subject: {self.subject}\n"
            f"Timestamp: {self.timestamp}\n"
            f"<UNTRUSTED_MESSAGE_BODY>\n{self.body}\n</UNTRUSTED_MESSAGE_BODY>"
        )
