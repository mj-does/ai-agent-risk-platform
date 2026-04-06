from agents.base_agent import BaseAgent


class GitHubAgent(BaseAgent):
    def __init__(self):
        super().__init__("GitHub Agent")

    def run(self, payload: dict):
        prompt = payload.get("prompt", "").lower()

        findings = []
        risk_flags = []

        # simple keyword-based analysis (can upgrade later)
        if "repo" in prompt or "github" in prompt:
            findings.append("Repository access detected")

        if "commit" in prompt or "push" in prompt:
            findings.append("Code modification action")

        if "secret" in prompt or "token" in prompt:
            findings.append("Potential secret exposure")
            risk_flags.append("secret_exposure")

        if "delete" in prompt:
            findings.append("Destructive action detected")
            risk_flags.append("destructive_action")

        return {
            "agent": "github",
            "findings": findings,
            "risk_flags": risk_flags,
            "raw_prompt": prompt,
            "metadata": payload
        }