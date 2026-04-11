import base64
import re
import zlib
from typing import Any, Dict

# Grouped patterns for explainability (injection / escalation / exfiltration / persistence)
_CATEGORY_PATTERNS: dict[str, list[str]] = {
    "injection": [
        r"ignore (?:all )?previous instructions",
        r"ignore (?:all )?prior instructions",
        r"disregard (?:the )?(?:above|prior|previous)",
        r"new instructions:",
        r"system prompt",
        r"reveal.*(?:system|prompt|instructions|secrets)",
        r"show.*(?:system|prompt|instructions|secrets)",
        r"leak.*(?:system|prompt|instructions|secrets)",
        r"jailbreak",
        r"dan mode",
    ],
    "escalation": [
        r"bypass security",
        r"give.*admin",
        r"full admin",
        r"root access",
        r"elevate.*privilege",
        r"maintenance.*override",
        r"unrestricted access",
        r"disable.*(?:monitoring|logging|audit)",
        r"operator override",
    ],
    "exfiltration": [
        r"exfiltrat(?:e|ion)",
        r"send.*(?:customer|user|client).*(?:data|database|records)",
        r"export.*(?:customer|user|client).*(?:data|database|records)",
        r"dump.*(?:customer|user|client).*(?:data|database|records)",
        r"(?:email|mail).*(?:customer|user|client).*(?:data|database|records)",
        r"send.*(?:database|db).*(?:email|mail)",
        r"download.*(?:user|customer).*(?:data|csv|dump)",
    ],
    "persistence": [
        r"install.*malware",
        r"backdoor",
        r"cron.*(?:job|tab)",
        r"startup.*script",
        r"hidden.*process",
        r"persist(?:ence|ent)?.*(?:access|shell)",
    ],
}

# High-impact regex (large score jump)
_HIGH_EXTRA: list[str] = [
    r"execute.*shell",
    r"run.*bash",
    r"delete.*database",
    r"drop.*table",
    r"production.*database",
    r"download.*script",
]

# Medium tier (smaller jump, often ambiguous — good LLM disambiguation candidates)
_MEDIUM_PATTERNS: list[str] = [
    r"\bdownload\b",
    r"\bexecute\b",
    r"admin access",
    r"\bserver\b",
    r"\bproduction\b",
    r"\bdatabase\b",
]

# Heuristic “no regex hit but shape looks off”
_SUSPICIOUS_SHAPE: list[str] = [
    r"pretend you (?:are|were)",
    r"new persona",
    r"adopt (?:a )?(?:new )?persona",
    r"roleplay",
    r"you are now",
    r"acting as",
    r"maintenance mode",
    r"decode the following",
    r"base64",
    r"disregard.*(?:safety|rules|policy)",
    r"unrestricted",
    r"without restrictions",
    r"for educational purposes only",
    r"ignore (?:your|the) (?:guidelines|rules)",
]


def _count_numbered_steps(text: str) -> int:
    return len(re.findall(r"(?m)^\s*\d+[\.)]\s+\S", text))


def _fingerprint_nudge(text: str, base: float) -> float:
    """Stable per-prompt spread so similar-looking prompts don't collapse to one score."""
    raw = (text or "").encode("utf-8", errors="ignore")
    c = zlib.crc32(raw) & 0xFFFFFFFF
    span = (c % 37) / 200.0  # 0 .. 0.185
    damp = 0.55 + 0.45 * (1.0 - min(1.0, base))
    return min(1.0, base + span * damp)


def _looks_like_base64_blob(text: str) -> bool:
    """Very loose: long alphanumeric+/+= token."""
    for m in re.finditer(r"[A-Za-z0-9+/]{40,}={0,2}", text):
        frag = m.group(0)
        if len(frag) < 48:
            continue
        try:
            base64.b64decode(frag, validate=True)
            return True
        except Exception:
            continue
    return False


def analyze_prompt_layers(prompt: str) -> Dict[str, Any]:
    """
    Regex-first analysis with category labels and uncertainty signals.
    """
    p = prompt or ""
    low = p.lower()

    categories_hit: list[str] = []
    high_tier_matched = False
    medium_hit = False

    score = 0.04

    for cat, pats in _CATEGORY_PATTERNS.items():
        hits = sum(1 for pat in pats if re.search(pat, low))
        if hits:
            if cat not in categories_hit:
                categories_hit.append(cat)
            high_tier_matched = True
            cat_pts = 0.14 + min(hits - 1, 4) * 0.055
            score += min(0.36, cat_pts)

    high_hits = sum(1 for pat in _HIGH_EXTRA if re.search(pat, low))
    if high_hits:
        high_tier_matched = True
        score += min(0.4, 0.12 + high_hits * 0.11)

    med_hits = sum(1 for pat in _MEDIUM_PATTERNS if re.search(pat, low))
    if med_hits:
        medium_hit = True
        score += min(0.32, med_hits * 0.065)

    score += min(0.07, len(p) / 900.0)

    score = _fingerprint_nudge(p, float(score))
    score = min(float(score), 1.0)

    regex_matched = high_tier_matched or medium_hit

    suspicious_shape = False
    for pat in _SUSPICIOUS_SHAPE:
        if re.search(pat, low):
            suspicious_shape = True
            break
    if _count_numbered_steps(p) >= 3:
        suspicious_shape = True
    if _looks_like_base64_blob(p):
        suspicious_shape = True
    if len(p) > 320 and not regex_matched:
        suspicious_shape = True

    # Uncertainty: structure looks risky but regex did not strongly fire
    review_required = (not high_tier_matched) and suspicious_shape

    # No strong/medium regex hit, but enough text that paraphrased or uncommon-word
    # attacks might be present — LLM semantic fallback can still run (if API keys exist).
    # Cap by injection_score so long benign prompts (creative writing, etc.) that only pick up
    # fingerprint/length noise are not sent to the LLM on every request.
    word_n = len(re.findall(r"\b\w+\b", low))
    semantic_uncertain = (
        not high_tier_matched
        and not regex_matched
        and len(p.strip()) >= 36
        and word_n >= 8
        and score < 0.2
    )

    return {
        "injection_score": score,
        "regex_matched": regex_matched,
        "high_tier_matched": high_tier_matched,
        "medium_tier_matched": medium_hit,
        "categories_hit": categories_hit,
        "suspicious_structure": suspicious_shape,
        "review_required": review_required,
        "semantic_uncertain": semantic_uncertain,
    }


def calculate_risk_score(prompt: str) -> float:
    return float(analyze_prompt_layers(prompt)["injection_score"])
