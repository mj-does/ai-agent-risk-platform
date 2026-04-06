from agents.base_agent import BaseAgent

class TerraformAgent(BaseAgent):
    def __init__(self):
        super().__init__("Terraform Agent")

    def analyze_prompt(self, prompt: str):
        if "infrastructure" in prompt or "deploy" in prompt:
            return "Terraform Action Requested"
        return "No infra action"
# Agent for managing Terraform resources
from .base_agent import BaseAgent

class TerraformAgent(BaseAgent):
    pass
