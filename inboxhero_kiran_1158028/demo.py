import argparse

from app.drafting import draft_reply
from app.gating import ActionGate
from app.preferences import set_preference
from app.reports import build_dashboard, explain_decisions, morning_digest, phishing_quarantine, sender_analytics
from app.storage import load_messages, save_decisions
from app.triage import triage_with_trace


def run_r1(dry_run=False, msg_id=None):
    messages = load_messages()
    selected = [m for m in messages if not msg_id or m.id == msg_id]

    if msg_id and not selected:
        print(f"Message {msg_id} not found in inbox.")
        return

    decisions = {}
    rule_count = 0

    print(f"{'ID':<7} | {'Disposition':<10} | Reason")
    print("-" * 72)

    for message in selected:
        from app.triage import fast_triage
        if fast_triage(message) is not None:
            rule_count += 1

        result = triage_with_trace(message, "R1")
        decisions[message.id] = {
            "disposition": result.disposition,
            "reason": result.reason,
        }
        print(f"{message.id:<7} | {result.disposition:<10} | {result.reason}")

    undecided = sum(not item["disposition"] for item in decisions.values())
    print(f"\nundecided: {undecided}")
    print(f"rule_handled: {rule_count} messages never reached the LLM")

    if not msg_id:
        save_decisions(decisions)


def run_r3(dry_run):
    gate = ActionGate(dry_run=dry_run)
    print("Simulating a proposed irreversible action (send)...")
    gate.propose(
        "send",
        "m999",
        {
            "to": "boss@paperjet.io",
            "subject": "Resignation",
            "body": "I quit.",
        },
        "R3",
    )
    if dry_run:
        print("outbox/ writes: 0")


def run_r4():
    set_preference("legal_mail", "always CC co-founder on Legal mail")
    print("Preference saved: 'always CC co-founder on Legal mail'")


def run_all(dry_run=False):
    messages = load_messages()

    print("=== R1: Zero the inbox ===")
    run_r1(dry_run)

    print("\n=== R2: Grounded reply (m008) ===")
    draft, cited = draft_reply(messages, "m008")
    if draft:
        print("\n--- DRAFT ---")
        print(draft)
        print(f"\ncited: {cited}")
    else:
        print("No grounded draft could be produced.")

    print("\n=== R3: Gate the irreversible ===")
    run_r3(dry_run)

    print("\n=== R4: Persistent preference ===")
    run_r4()

    print("\n=== R5: Refuse embedded instructions ===")
    run_r1(dry_run)

    print("\n=== R6: Dashboard ===")
    build_dashboard(messages)

    print("\n=== X1: Sender Analytics ===")
    sender_analytics(messages)

    print("\n=== X2: Morning Digest ===")
    morning_digest(messages)

    print("\n=== X3: Phishing Quarantine ===")
    phishing_quarantine(messages)

    print("\n=== X4: Decision Explainer ===")
    explain_decisions(messages)


def main():
    parser = argparse.ArgumentParser(description="InboxHero independent implementation")
    parser.add_argument("--cap", choices=("R1", "R2", "R3", "R4", "R5", "R6", "X1", "X2", "X3", "X4"))
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--msg")
    args = parser.parse_args()

    if args.all:
        run_all(args.dry_run)
        return

    if not args.cap:
        parser.error("Provide --cap or --all")

    messages = load_messages()

    if args.cap == "R1":
        run_r1(args.dry_run, args.msg)
    elif args.cap == "R2":
        if not args.msg:
            parser.error("R2 requires --msg")
        draft, cited = draft_reply(messages, args.msg)
        if draft:
            print("\n--- DRAFT ---")
            print(draft)
            print(f"\ncited: {cited}")
        else:
            print("The system could not produce a grounded draft.")
    elif args.cap == "R3":
        run_r3(args.dry_run)
    elif args.cap == "R4":
        run_r4()
    elif args.cap == "R5":
        print("Scanning inbox for embedded assistant-directed instructions...")
        run_r1(args.dry_run, args.msg)
    elif args.cap == "R6":
        build_dashboard(messages)
    elif args.cap == "X1":
        sender_analytics(messages)
    elif args.cap == "X2":
        morning_digest(messages)
    elif args.cap == "X3":
        phishing_quarantine(messages)
    elif args.cap == "X4":
        explain_decisions(messages, args.msg)


if __name__ == "__main__":
    main()
