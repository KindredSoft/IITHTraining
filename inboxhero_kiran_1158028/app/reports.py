from collections import Counter
from html import escape

from app.llm import generate_object, generate_text
from app.security import looks_like_phishing
from app.storage import append_event, load_decisions, read_events


def sender_analytics(messages):
    counts = Counter()
    for message in messages:
        if message.unread:
            domain = message.sender.split("@", 1)[-1] if "@" in message.sender else "unknown"
            counts[domain] += 1

    print("\n--- X1: Unread Messages by Domain ---")
    for domain, count in sorted(counts.items(), key=lambda pair: (-pair[1], pair[0])):
        print(f"{domain:<30} : {count}")

    append_event("X1", "sender_analytics", {"domains": dict(counts)})


def morning_digest(messages):
    needs = []
    archived = 0

    for message in messages:
        if not message.unread:
            continue
        from app.triage import fast_triage
        quick = fast_triage(message)
        if quick and quick.disposition == "archive":
            archived += 1
        else:
            needs.append(message)

    print("\n--- X2: Morning Digest ---")
    print(f"Auto-archived {archived} low-priority messages.")
    print(f"\n{len(needs)} messages need your attention:")
    for message in needs[:5]:
        print(f" - {message.sender}: {message.subject}")
    if len(needs) > 5:
        print(f"   ... and {len(needs) - 5} more.")

    append_event("X2", "morning_digest", {
        "auto_archived": archived,
        "needs_attention_count": len(needs),
    })


def phishing_quarantine(messages):
    hits = [
        message for message in messages
        if looks_like_phishing(message.subject, message.body)
    ]

    print("\n--- X3: Phishing Quarantine ---")
    if not hits:
        print("No phishing attempts detected.")
    for message in hits:
        print(f"QUARANTINED: {message.id} from {message.sender} - {message.subject}")
        append_event("X3", "quarantine", {
            "message_id": message.id,
            "reason": "Suspicious keyword pattern",
        })


def explain_decisions(messages, message_id=None):
    decisions = load_decisions()
    by_id = {message.id: message for message in messages}

    if message_id:
        targets = [message_id] if message_id in decisions else []
        if not targets:
            print(f"No decision recorded for {message_id}. Run R1 first.")
            return
    else:
        targets = [
            mid for mid, decision in decisions.items()
            if decision.get("disposition") == "escalate"
        ]
        if not targets:
            print("No escalated messages found. Try --msg <id> for a specific message.")
            return
        print(f"Explaining {len(targets)} escalated messages (candidates for human review):\n")

    refusal_ids = {
        event.get("details", {}).get("message_id")
        for event in read_events()
        if event.get("event") == "refusal"
    }

    for mid in targets:
        decision = decisions[mid]
        message = by_id.get(mid)
        if not message:
            continue

        prompt = f"""
Explain this email triage decision to a non-technical user in 2-3 short sentences.
Message: {message.subject}
Body: {message.body[:250]}
Disposition: {decision.get('disposition')}
Reason: {decision.get('reason')}
Mention that human review is appropriate if the message was escalated.
"""
        explanation = generate_text(prompt).strip()
        if not explanation:
            explanation = (
                f"The message was marked {decision.get('disposition', 'unknown')} because "
                f"{decision.get('reason', 'no reason was recorded')}. "
                "Review the message manually before taking any action."
            )

        print(f"--- {mid} -> {decision.get('disposition', '?').upper()} ---")
        print(f"From: {message.sender} | Subject: {message.subject}")
        print(f"Explanation: {explanation}")
        if mid in refusal_ids:
            print("WARNING: Also flagged as prompt injection attempt.")
        print()

        append_event("X4", "explanation", {
            "message_id": mid,
            "disposition": decision.get("disposition"),
        })


def build_dashboard(messages):
    events = list(read_events())
    gate_events = [event.get("details", {}) for event in events if event.get("event") == "gate"]

    flagged = []
    seen = set()
    for event in events:
        if event.get("event") != "refusal":
            continue
        details = event.get("details", {})
        mid = details.get("message_id")
        if mid and mid not in seen:
            seen.add(mid)
            flagged.append(details)

    decisions = load_decisions()
    commitments = []
    for message in messages:
        if not message.unread:
            continue
        text = message.body.lower()
        if any(marker in text for marker in (
            "by the", "scheduled", "deadline", "need sam", "can you", "please review",
            "confirming", "signature", "approve", "reminder",
        )):
            commitments.append({
                "date": _extract_date_hint(message.body),
                "description": message.body.split(".")[0].strip(),
                "cited": message.id,
            })

    pending_items = "".join(
        f"<li><strong>{escape(str(item.get('message_id', '?')))}</strong>: "
        f"proposed '{escape(str(item.get('proposed_action', 'unknown')))}' - "
        f"{'approved' if item.get('approved') else 'rejected'}.</li>"
        for item in gate_events
    ) or "<li>No gate decisions recorded yet.</li>"

    flagged_items = "".join(
        f"<li><strong>{escape(str(item.get('message_id')))}</strong>: "
        f"assistant-directed instruction was refused and left untouched.</li>"
        for item in flagged
    ) or "<li>No embedded assistant instructions have been flagged.</li>"

    commitment_items = "".join(
        f"<li><b>{escape(item['date'])}</b>: {escape(item['description'])} "
        f"[cited: {escape(item['cited'])}]</li>"
        for item in commitments[:25]
    ) or "<li>No obvious commitments detected.</li>"

    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>InboxHero Dashboard</title>
<style>
body {{ font-family: system-ui, sans-serif; max-width: 1000px; margin: 2rem auto; padding: 0 1rem; }}
section {{ border: 1px solid #ddd; border-radius: 10px; padding: 1rem; margin: 1rem 0; }}
h1 {{ margin-bottom: 1.5rem; }}
</style>
</head>
<body>
<h1>InboxHero Dashboard</h1>
<section><h2>Pending Actions</h2><ul>{pending_items}</ul></section>
<section><h2>Flagged</h2><ul>{flagged_items}</ul></section>
<section><h2>Commitments</h2><ul>{commitment_items}</ul></section>
</body>
</html>
"""
    from config import BASE_DIR
    output = BASE_DIR / "dashboard.html"
    output.write_text(html, encoding="utf-8")
    append_event("R6", "dashboard_generated", {
        "panes": ["pending", "flagged", "commitments"],
        "decision_count": len(decisions),
    })
    print("Dashboard generated: dashboard.html")


def _extract_date_hint(body: str) -> str:
    lowered = body.lower()
    for hint in ("last night", "by friday", "by monday", "the 12th", "the 14th", "the 18th", "the 20th"):
        if hint in lowered:
            return hint
    return "not specified"
