# Capability Matrix

The implementation keeps the assignment-facing capability IDs and CLI commands while using a different internal design.

| ID | Capability | Command | Observable |
|---|---|---|---|
| R1 | Zero the inbox | `python demo.py --cap R1` | Every message gets one disposition and reason; `decisions.json` is persisted |
| R2 | Grounded reply | `python demo.py --cap R2 --msg m008` | Draft is derived only from earlier messages in the same thread and prints cited IDs |
| R3 | Gate irreversible actions | `python demo.py --cap R3 --dry-run` | Send/delete proposals pass through an explicit approval gate; dry-run writes no outbox file |
| R4 | Persistent preference | `python demo.py --cap R4` | Preference survives process exit in `data/preferences.json` |
| R5 | Refuse embedded instructions | `python demo.py --cap R5` | Assistant-directed instructions are refused, logged, and not acted upon |
| R6 | Dashboard | `python demo.py --cap R6` | `dashboard.html` contains pending, flagged, and commitment panes |
| X1 | Sender analytics | `python demo.py --cap X1` | Unread counts grouped by sender domain |
| X2 | Morning digest | `python demo.py --cap X2` | Separates low-priority auto-archive candidates from attention items |
| X3 | Phishing quarantine | `python demo.py --cap X3` | Suspicious password/payment requests are surfaced as quarantined |
| X4 | Decision explainer | `python demo.py --cap X4` | Uses persisted decisions and trace data to explain escalations |

## Safety boundary

Only `ActionGate.propose()` can perform the assignment's irreversible actions. Model output is treated as a proposal, never as direct authority to write to the outbox or delete data.
