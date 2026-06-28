import json
import os
from datetime import datetime, timezone
from config import LOG_FILE, LLM_MODEL


def log_interaction(question: str, tier: str, response: str) -> None:
    """
    Append a structured record of this interaction to the audit log.

    TODO — Milestone 3:

    Before writing any code, complete specs/auditor-spec.md. The key decisions
    are what fields to log, how much of the question and response to include,
    and how to handle the logs/ directory not existing yet.

    Each record should be a JSON object written as a single line to LOG_FILE
    (defined in config.py as "logs/audit.jsonl").

    Required fields:
      - "timestamp"        : ISO 8601 datetime string
      - "tier"             : the safety tier assigned to this question
      - "question"         : the user's question (truncate to 300 chars if longer)
      - "response_preview" : first 200 characters of the response

    If the logs/ directory doesn't exist, create it before writing.

    Also print a one-line summary to the terminal so you can see logged
    interactions in real time without opening the file:
      e.g. [LOGGED] tier=caution | "How do I replace a faucet?" → 47 chars

    Design your log entry in specs/auditor-spec.md before implementing here.
    """
    # Build the structured record. Question is capped at 300 chars, the response
    # preview at 200 — but we keep the full length separately for diagnostics.
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "tier": tier,
        "question": question[:300],
        "response_preview": response[:200],
        "model": LLM_MODEL,
        "response_length": len(response),
    }

    # Self-heal: create logs/ if it doesn't exist so logging never crashes the app.
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

    # Append one JSON object per line (JSONL) — never rewrite the whole file.
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

    # One-line terminal summary so logged interactions are visible in real time.
    q_preview = question[:50] + ("..." if len(question) > 50 else "")
    print(f'[LOGGED] tier={tier} | "{q_preview}" | {len(response)} chars')
