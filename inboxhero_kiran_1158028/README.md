# InboxHero
https://github.com/KindredSoft/IITHTraining

## Architecture

```text
demo.py
  ├── app/triage.py        -> fast rules + model-backed triage
  ├── app/security.py      -> prompt-injection and phishing checks
  ├── app/drafting.py      -> deterministic thread retrieval + grounded drafting
  ├── app/gating.py        -> irreversible-action approval boundary
  ├── app/storage.py       -> JSON/JSONL persistence
  └── app/reports.py       -> analytics, digest, quarantine, dashboard, explanations
```

The important design decision is that the LLM is never given authority to perform filesystem or mailbox actions. It returns structured reasoning; Python validates the result and decides whether an action is allowed.

## Setup

### 1. Create an environment

```bash
python -m venv .venv
```

Windows:

```powershell
.venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Local model

The default provider is Ollama. Install Ollama separately and make sure it is running, then:

```bash
ollama pull phi3
```

### 4. Optional Gemini

Copy `.env.example` to `.env`, then configure:

```text
INBOXHERO_LLM=gemini
INBOXHERO_MODEL=gemini-2.5-flash
GEMINI_API_KEY=...
```

## Commands

```bash
python demo.py --cap R1
python demo.py --cap R2 --msg m008
python demo.py --cap R3 --dry-run
python demo.py --cap R4
python demo.py --cap R5
python demo.py --cap R6
python demo.py --cap X1
python demo.py --cap X2
python demo.py --cap X3
python demo.py --cap X4
python demo.py --all --dry-run
```

For a targeted triage:

```bash
python demo.py --cap R1 --msg m015
```

## Persistence

- `data/inbox.json` — assignment input fixture
- `data/preferences.json` — persistent user preferences
- `runtime/decisions.json` — latest R1 decisions
- `runtime/trace.jsonl` — append-only audit trail
- `outbox/` — mock sent-message output

Runtime files are deliberately separated from input data.

## Grounded drafting

R2 retrieves only messages in the target's `thread_id` whose timestamps are earlier than the target. The model/fallback can cite only those retrieved messages. It cannot use unrelated inbox messages as grounding.

## Prompt-injection handling

The email body is treated as untrusted data. Assistant-directed instructions are detected before a decision is accepted, and the system forces an `escalate` result. The message remains untouched and a refusal event is written to the trace.

## Error handling

Malformed JSON model output falls back to a deterministic local decision path. Missing messages, malformed inbox files, invalid dispositions, unavailable LLM services, and rejected irreversible actions are handled without silently executing a risky operation.

## Testing

The project has no web service and does not require a database. The capability commands are the primary acceptance checks. A useful smoke-test sequence is:

```bash
python demo.py --cap R3 --dry-run
python demo.py --cap R2 --msg m008
python demo.py --cap R4
python demo.py --cap R1 --msg m015
python demo.py --cap R5
python demo.py --cap R6
python demo.py --cap X1
python demo.py --cap X2
python demo.py --cap X3
python demo.py --cap X4
```

### 1. What did you refuse to automate?
The system does not perform irreversible actions automatically. Sending is placed behind `ActionGate`; the system proposes the action and asks for explicit user approval before writing to `outbox/`. Draft generation is automated, while phishing messages are flagged and left untouched.

### 2. Where does untrusted text enter your system?
The email body is treated as untrusted data. `app/security.py` checks the body for assistant-directed instructions and prompt-injection patterns before a decision is accepted. Detected injection attempts force an `escalate` result, so the message is not acted on.

### 3. Who is accountable when it sends the wrong thing?
The user provides the final approval for an irreversible send. The system does not give the LLM direct permission to send messages; proposed actions and approval decisions are recorded in `runtime/trace.jsonl`, providing an audit trail.

### 4. Name your own machinery.
No agent framework such as CrewAI is used. `demo.py` is the entry point, `app/triage.py` handles triage, `app/security.py` handles security checks, `app/drafting.py` handles grounded drafts, `app/gating.py` provides the approval boundary, `app/storage.py` handles persistence, and `app/reports.py` generates analytics and reports.
