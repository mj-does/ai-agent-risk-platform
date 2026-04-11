from collections import defaultdict
from typing import Any, Dict, Optional

# In-memory session store (demo / single-node). Resets on process restart.
_HISTORY: dict[str, list[str]] = defaultdict(list)


def record_prompt(session_id: Optional[str], prompt: str) -> Dict[str, Any]:
    if not session_id or not (prompt or "").strip():
        return {
            "recent_prompts": [],
            "pattern_risk_bonus": 0,
            "pattern_note": None,
        }

    hist = _HISTORY[session_id]
    hist.append((prompt or "").strip())
    while len(hist) > 3:
        hist.pop(0)

    bonus = 0
    note = None
    if len(hist) >= 2:
        combined = " ".join(h.lower() for h in hist)
        recon = sum(
            1
            for k in (
                "list",
                "show files",
                "directory",
                "folder",
                "ls ",
                "dir ",
                "enumerate",
            )
            if k in combined
        )
        sensitive = sum(
            1
            for k in (
                "config",
                "secret",
                "api key",
                "credential",
                "password",
                "export",
                "dump",
                "send to",
                "email",
                "exfil",
            )
            if k in combined
        )
        if len(hist) == 3 and recon >= 1 and sensitive >= 2:
            bonus = 15
            note = (
                "Session pattern: multiple prompts suggest reconnaissance then "
                "sensitive extraction — elevated risk."
            )
        elif len(hist) >= 2 and sensitive >= 2:
            bonus = 8
            note = "Session pattern: repeated sensitive-data requests."

    return {
        "recent_prompts": list(hist),
        "pattern_risk_bonus": bonus,
        "pattern_note": note,
    }
