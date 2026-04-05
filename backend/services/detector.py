import re

SUSPICIOUS_PATTERNS = [
    r"ignore\s+.*?(?:instructions|directives|prompts)",
    r"act\s+as\s+.*?(?:system|admin|root|superuser)",
    r"(?:reveal|show|display|tell\s+me)\s+.*?(?:prompt|instructions|secrets|hidden\s+commands)",
    r"bypass\s+.*?(?:security|filters|restrictions)",
    r"execute\s+.*?(?:command|script|code)",
    r"drop\s+.*?table",
    r"delete\s+.*?from",
]

def detect_injection(prompt: str):
    prompt_lower = prompt.lower()
    for pattern in SUSPICIOUS_PATTERNS:
        if re.search(pattern, prompt_lower):
            return True, f"Pattern matched: {pattern}"
    return False, None
