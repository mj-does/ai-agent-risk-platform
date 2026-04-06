def check_policies(agent_output: dict):
    """
    Evaluates policy compliance based on agent findings and metadata
    """

    metadata = agent_output.get("metadata", {})
    industry = metadata.get("industry", "").lower()
    risk_flags = agent_output.get("risk_flags", [])

    # industry-specific policies
    policy_map = {
        "finance": ["GDPR", "EU AI Act"],
        "healthcare": ["HIPAA", "EU AI Act"],
        "hr": ["GDPR", "Bias & Fairness Guidelines"]
    }

    applicable_policies = policy_map.get(industry, ["General AI Guidelines"])

    violations = []

    # 🚨 Rule-based violations
    if "secret_exposure" in risk_flags:
        violations.append("Sensitive data exposure violation")

    if "destructive_action" in risk_flags:
        violations.append("Unauthorized destructive action")

    if "public_access" in risk_flags:
        violations.append("Public access misconfiguration")

    if "high_impact" in risk_flags and industry == "finance":
        violations.append("High-risk action in financial system")

    # final status
    status = "fail" if violations else "pass"

    return {
        "status": status,
        "violations": violations,
        "policies_checked": applicable_policies
    }