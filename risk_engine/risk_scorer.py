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