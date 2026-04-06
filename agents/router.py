from agents.github_agent import GitHubAgent
from agents.terraform_agent import TerraformAgent
from policy_engine.policy_checker import check_policies
from risk_engine.risk_scorer import score_risk

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

        # 1. choose agent
        agent = self.route(prompt)

        # 2. run agent (IMPORTANT: your agents must support this)
        agent_output = agent.run(payload)

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