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

    prompt = payload.get("prompt", "").lower()
    description = payload.get("use_case", "").lower()
    ai_model = payload.get("agent_name", "").lower()
    industry = payload.get("industry", "").lower()

    risk_flags = agent_output.get("risk_flags", [])
    violations = policy_output.get("violations", [])
    injection_score = agent_output.get("injection_score", 0.0) or 0.0
    try:
        injection_score = float(injection_score)
    except Exception:
        injection_score = 0.0

    # 🔴 Prompt-injection / privilege escalation signals (high weight)
    if injection_score >= 0.4:
        # scale 0–1 detector into up to +60 points
        risk_score += int(round(min(1.0, injection_score) * 60))
        risks.append("Prompt injection patterns detected")

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

    if "public_access" in risk_flags:
        risk_score += 25
        risks.append("Public exposure risk")

    if "high_impact" in risk_flags:
        risk_score += 20
        risks.append("High impact operation")

    if "prompt_injection" in risk_flags and injection_score < 0.4:
        risk_score += 20
        risks.append("Suspicious instruction override attempt")

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

    # 🟢 Normalize risk level
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