from agents.base_agent import BaseAgent

class GitHubAgent(BaseAgent):
    def __init__(self):
        super().__init__("GitHub Agent")

    def analyze_prompt(self, prompt: str):
        if "repo" in prompt or "commit" in prompt:
            return "GitHub Action Requested"
        return "No GitHub action"