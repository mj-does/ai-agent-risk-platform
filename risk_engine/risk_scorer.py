import zlib


def score_risk(agent_output: dict, policy_output: dict, payload: dict):
    """
    Advanced risk scoring using:
    - Agent findings
    - Risk flags
    - Policy violations
    - Metadata (model, industry, use case)
    """

    risk_score = 0
    risks = []

    prompt_raw = payload.get("prompt", "") or ""
    prompt = prompt_raw.lower()
    description = payload.get("use_case", "").lower()
    ai_model = payload.get("agent_name", "").lower()
    industry = payload.get("industry", "").lower()

    risk_flags = agent_output.get("risk_flags", [])
    attack_categories = agent_output.get("attack_categories") or []
    violations = policy_output.get("violations", [])
    injection_score = agent_output.get("injection_score", 0.0) or 0.0
    try:
        injection_score = float(injection_score)
    except Exception:
        injection_score = 0.0

    # 🔴 Prompt-injection / privilege escalation signals (graduated for score spread)
    if injection_score >= 0.4:
        risk_score += int(round(min(1.0, injection_score) * 58))
        risks.append("Prompt injection patterns detected")
    elif injection_score >= 0.28:
        risk_score += int(round((injection_score - 0.28) / 0.12 * 34))
        risks.append("Elevated injection / misuse signals")
    elif injection_score >= 0.16:
        risk_score += int(round((injection_score - 0.16) / 0.12 * 22))
        risks.append("Low–moderate structural risk from prompt heuristics")

    if "privilege_escalation" in risk_flags:
        risk_score += 25
        risks.append("Privilege escalation attempt")

    # 🔴 Agent-based risks
    if "destructive_action" in risk_flags:
        risk_score += 40
        risks.append("Destructive action detected")

    if "secret_exposure" in risk_flags:
        risk_score += 35
        risks.append("Sensitive data exposure")

    if "data_exfiltration" in risk_flags:
        risk_score += 35
        risks.append("Data exfiltration attempt")

    if "public_access" in risk_flags:
        risk_score += 25
        risks.append("Public exposure risk")

    if "high_impact" in risk_flags:
        risk_score += 20
        risks.append("High impact operation")

    if "prompt_injection" in risk_flags and injection_score < 0.4:
        risk_score += 20
        risks.append("Suspicious instruction override attempt")

    if isinstance(attack_categories, (list, tuple)) and attack_categories:
        label = ", ".join(str(c) for c in attack_categories if c)
        if label:
            risks.append(f"Attack pattern categories: {label}")

    # 🟠 Policy violations
    violation_count = len(violations)
    if violation_count > 0:
        risk_score += violation_count * 15
        risks.append(f"{violation_count} policy violations detected")

    # 🟡 Context-based risks (your original logic improved)
    if "auto" in description:
        risk_score += 10
        risks.append("High automation impact")

    if "reject" in description:
        risk_score += 15
        risks.append("Potential bias / unfair decisions")

    if ai_model in ["gpt-4", "claude", "gemini"]:
        risk_score += 10
        risks.append("Uses powerful foundation model")

    if industry in ["healthcare", "finance", "hr"]:
        risk_score += 15
        risks.append("Sensitive industry")

    # Spread similar prompts across a wider point band (deterministic, audit-stable)
    crc = zlib.crc32(prompt_raw.encode("utf-8", errors="ignore")) & 0xFFFF
    risk_score += (crc % 13) - 6

    # 🟢 Normalize risk level
    risk_score = max(0, min(100, int(risk_score)))

    if risk_score >= 70:
        level = "HIGH"
    elif risk_score >= 40:
        level = "MEDIUM"
    else:
        level = "LOW"

    return {
        "risk_score": risk_score,
        "risk_level": level,
        "risks_identified": list(set(risks))  # remove duplicates
    }