import re

HIGH_RISK_PATTERNS = [
    r"ignore previous instructions",
    r"ignore all previous instructions",
    r"bypass security",
    r"reveal.*(?:system|prompt|instructions|secrets)",
    r"show.*(?:system|prompt|instructions|secrets)",
    r"leak.*(?:system|prompt|instructions|secrets)",
    r"exfiltrat(?:e|ion)",
    r"install.*malware",
    r"download.*script",
    r"execute.*shell",
    r"delete.*database",
    r"drop.*table",
    r"give.*admin",
    r"production.*database",
    r"run.*bash",
]

MEDIUM_RISK_PATTERNS = [
    r"download",
    r"execute",
    r"admin access",
    r"server",
    r"production",
    r"database",
]

def calculate_risk_score(prompt: str) -> float:
    prompt_lower = prompt.lower()
    score = 0.05  # base risk

    # HIGH RISK matches → big jump
    for pattern in HIGH_RISK_PATTERNS:
        if re.search(pattern, prompt_lower):
            score += 0.35

    # MEDIUM RISK matches → smaller jump
    for pattern in MEDIUM_RISK_PATTERNS:
        if re.search(pattern, prompt_lower):
            score += 0.15

    # long prompts slightly riskier
    if len(prompt) > 150:
        score += 0.05

    return min(score, 1.0)