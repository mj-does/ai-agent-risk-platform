class BaseAgent:
    def __init__(self, name):
        self.name = name

    def analyze_prompt(self, prompt: str):
        raise NotImplementedError("Subclasses must implement this")

    def decide_action(self, risk_score: float):
        """
        Decision policy used by ALL agents
        """
        if risk_score > 0.8:
            return "BLOCK"
        elif risk_score > 0.5:
            return "RESTRICT"
        else:
            return "ALLOW"
# Base agent class with shared functionality
class BaseAgent:
    pass
