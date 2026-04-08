from agents.github_agent import GitHubAgent
from agents.terraform_agent import TerraformAgent
from policy_engine.policy_checker import check_policies
from risk_engine.risk_scorer import score_risk
from agents.prompt_injection_detector import calculate_risk_score

# comment this for now if import is failing
# from tiger_client import store_in_graph


class Router:
    def __init__(self):
        self.github_agent = GitHubAgent()
        self.terraform_agent = TerraformAgent()

    def route(self, prompt: str):
        prompt_lower = prompt.lower()

        github_keywords = [
            "repo", "github", "commit", "push", "pull request", "readme"
        ]

        terraform_keywords = [
            "deploy", "infrastructure", "database", "server",
            "production", "cloud", "admin", "install", "execute"
        ]

        if any(word in prompt_lower for word in github_keywords):
            return self.github_agent

        if any(word in prompt_lower for word in terraform_keywords):
            return self.terraform_agent

        return self.terraform_agent  # default

    def run(self, payload: dict):
        prompt = payload.get("prompt", "")

        # 0. prompt injection / privilege escalation signal
        injection_score = calculate_risk_score(prompt)  # 0–1

        # 1. choose agent
        agent = self.route(prompt)

        # 2. run agent (IMPORTANT: your agents must support this)
        agent_output = agent.run(payload)

        # Merge injection signal into agent_output so policy + risk scorer can use it.
        # Keep this lightweight and deterministic (regex-based).
        agent_output = dict(agent_output or {})
        agent_output["injection_score"] = injection_score
        rf = list(agent_output.get("risk_flags", []) or [])
        if injection_score >= 0.6 and "prompt_injection" not in rf:
            rf.append("prompt_injection")
        if ("admin" in prompt.lower() or "full admin" in prompt.lower()) and "privilege_escalation" not in rf:
            rf.append("privilege_escalation")
        if any(k in prompt.lower() for k in ["system secret", "system secrets", "reveal", "exfiltrate", "api key", "token", "credentials"]):
            if "secret_exposure" not in rf:
                rf.append("secret_exposure")
        agent_output["risk_flags"] = rf

        # 3. policy check
        policy_result = check_policies(agent_output)

        # 4. risk scoring (using your existing function)
        risk_result = score_risk(
            agent_output,
            policy_result,
            payload
    )

        # 5. graph storage (optional for now)
        # try:
        #     store_in_graph(agent_output, risk_result)
        # except Exception as e:
        #     print(f"[Graph Error] {e}")

        return {
            "agent_used": agent.__class__.__name__,
            "agent_output": agent_output,
            "policy": policy_result,
            "risk": risk_result
        }