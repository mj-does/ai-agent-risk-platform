from agents.base_agent import BaseAgent


class TerraformAgent(BaseAgent):
    def __init__(self):
        super().__init__("Terraform Agent")

    def run(self, payload: dict):
        prompt = payload.get("prompt", "").lower()

        findings = []
        risk_flags = []

        if "deploy" in prompt or "infrastructure" in prompt:
            findings.append("Infrastructure deployment requested")

        if "production" in prompt:
            findings.append("Production environment change")
            risk_flags.append("high_impact")

        if "database" in prompt:
            findings.append("Database operation detected")

        if "delete" in prompt or "destroy" in prompt:
            findings.append("Infrastructure destruction detected")
            risk_flags.append("destructive_action")

        if "public" in prompt:
            findings.append("Public exposure risk")
            risk_flags.append("public_access")

        return {
            "agent": "terraform",
            "findings": findings,
            "risk_flags": risk_flags,
            "raw_prompt": prompt,
            "metadata": payload
        }