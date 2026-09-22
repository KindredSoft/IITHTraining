from pathlib import Path

from config import OUTBOX_DIR
from app.storage import append_event


class ActionGate:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run

    def propose(self, action: str, message_id: str, details: dict, capability: str) -> bool:
        if action not in {"send", "delete"}:
            raise ValueError("Only irreversible actions belong behind the action gate")

        print("\n--- PROPOSED IRREVERSIBLE ACTION ---")
        print(f"Action: {action}")
        print(f"Message ID: {message_id}")
        print(f"Details: {details}")

        if self.dry_run:
            approved = True
            print("[DRY-RUN] Approval simulated; no external state will be changed.")
        else:
            answer = input("Approve this action? (y/n): ").strip().lower()
            approved = answer == "y"

        append_event(
            capability,
            "gate",
            {
                "proposed_action": action,
                "message_id": message_id,
                "details": details,
                "approved": approved,
            },
        )

        if not approved:
            print("[REJECTED] Action aborted by user.")
            return False

        if self.dry_run:
            if action == "send":
                print(f"[DRY-RUN] Would write reply to outbox/{message_id}_reply.txt")
            else:
                print(f"[DRY-RUN] Would delete message {message_id}.")
            return True

        if action == "send":
            self._write_outbox(message_id, details)
        else:
            # The assignment fixture has no real mailbox API. We therefore
            # record approval rather than pretending a remote deletion happened.
            print(f"[EXECUTED] Delete approved for {message_id} (mock mailbox).")
        return True

    @staticmethod
    def _write_outbox(message_id: str, details: dict) -> None:
        path = Path(OUTBOX_DIR) / f"{message_id}_reply.txt"
        path.write_text(
            f"To: {details.get('to', '')}\n"
            f"Subject: {details.get('subject', '')}\n\n"
            f"{details.get('body', '')}",
            encoding="utf-8",
        )
        print(f"[EXECUTED] Sent message written to {path}")
