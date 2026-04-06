from agents.github_agent import GitHubAgent
from agents.terraform_agent import TerraformAgent

github_agent = GitHubAgent()
terraform_agent = TerraformAgent()

def route_prompt(prompt: str):
    prompt_lower = prompt.lower()

    # GitHub related actions
    github_keywords = [
        "repo", "github", "commit", "push", "pull request", "readme"
    ]

    # Infrastructure / system actions
    terraform_keywords = [
        "deploy", "infrastructure", "database", "server",
        "production", "cloud", "admin", "install", "execute"
    ]

    if any(word in prompt_lower for word in github_keywords):
        return github_agent

    if any(word in prompt_lower for word in terraform_keywords):
        return terraform_agent

    # Default fallback → send to Terraform (most dangerous)
    return terraform_agent