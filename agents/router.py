import re

from agents.github_agent import GitHubAgent
from agents.terraform_agent import TerraformAgent
from agents.llm_guard import llm_second_opinion, should_call_llm
from agents.prompt_injection_detector import analyze_prompt_layers
from agents.session_tracker import record_prompt
from policy_engine.policy_checker import check_policies
from risk_engine.risk_scorer import score_risk


class Router:
    def __init__(self):
        self.github_agent = GitHubAgent()
        self.terraform_agent = TerraformAgent()

    def route(self, prompt: str):
        prompt_lower = prompt.lower()

        github_keywords = [
            "repo",
            "github",
            "commit",
            "push",
            "pull request",
            "readme",
        ]

        terraform_keywords = [
            "deploy",
            "infrastructure",
            "database",
            "server",
            "production",
            "cloud",
            "admin",
            "install",
            "execute",
        ]

        if any(word in prompt_lower for word in github_keywords):
            return self.github_agent

        if any(word in prompt_lower for word in terraform_keywords):
            return self.terraform_agent

        return self.terraform_agent

    def run(self, payload: dict):
        prompt = payload.get("prompt", "") or ""
        session_id = payload.get("session_id")
        manual = (payload.get("manual_override") or "").strip().lower() or None

        sess = record_prompt(session_id, prompt)
        layers = analyze_prompt_layers(prompt)
        injection_score = float(layers["injection_score"])
        llm_result = None

        if should_call_llm(layers):
            llm_result = llm_second_opinion(prompt)
            if llm_result:
                injection_score = min(
                    1.0, injection_score + float(llm_result.get("injection_boost") or 0)
                )

        categories = list(layers.get("categories_hit") or [])
        if llm_result:
            for c in llm_result.get("categories") or []:
                if c in ("injection", "escalation", "exfiltration", "persistence"):
                    if c not in categories:
                        categories.append(c)

        if layers.get("review_required"):
            evaluation_status = "review_required"
        elif injection_score >= 0.45 or layers.get("high_tier_matched"):
            evaluation_status = "elevated"
        else:
            evaluation_status = "clear"

        agent = self.route(prompt)
        agent_output = dict(agent.run(payload) or {})
        agent_output["injection_score"] = injection_score
        agent_output["attack_categories"] = categories
        agent_output["session_pattern_risk_bonus"] = int(
            sess.get("pattern_risk_bonus") or 0
        )
        agent_output["session_pattern_note"] = sess.get("pattern_note")
        agent_output["recent_session_prompts"] = sess.get("recent_prompts") or []
        if llm_result:
            agent_output["llm_guard"] = {
                "used": True,
                "intent": llm_result.get("intent"),
                "confidence": llm_result.get("confidence"),
                "note": llm_result.get("note"),
            }
        else:
            agent_output["llm_guard"] = {"used": False}

        rf = list(agent_output.get("risk_flags", []) or [])
        if injection_score >= 0.6 and "prompt_injection" not in rf:
            rf.append("prompt_injection")
        if ("admin" in prompt.lower() or "full admin" in prompt.lower()) and "privilege_escalation" not in rf:
            rf.append("privilege_escalation")

        if "injection" in categories and "prompt_injection" not in rf:
            rf.append("prompt_injection")
        if "escalation" in categories and "privilege_escalation" not in rf:
            rf.append("privilege_escalation")
        if "exfiltration" in categories:
            if "data_exfiltration" not in rf:
                rf.append("data_exfiltration")
            if "secret_exposure" not in rf:
                rf.append("secret_exposure")
        if "persistence" in categories and "high_impact" not in rf:
            rf.append("high_impact")

        p = prompt.lower()
        if any(
            k in p
            for k in [
                "system secret",
                "system secrets",
                "api key",
                "token",
                "credentials",
                "password",
                "ssn",
                "credit card",
            ]
        ):
            if "secret_exposure" not in rf:
                rf.append("secret_exposure")

        exfil_patterns = [
            r"send.*customer.*(data|database|records).*email",
            r"send.*(database|db).*email",
            r"export.*customer.*(data|database|records)",
            r"dump.*customer.*(data|database|records)",
            r"exfiltrat(e|ion)",
        ]
        if any(re.search(ptn, p) for ptn in exfil_patterns):
            if "secret_exposure" not in rf:
                rf.append("secret_exposure")
            if "data_exfiltration" not in rf:
                rf.append("data_exfiltration")

        agent_output["risk_flags"] = rf

        policy_result = check_policies(agent_output)
        risk_result = score_risk(agent_output, policy_result, payload)

        risks = list(risk_result.get("risks_identified") or [])
        bonus = int(sess.get("pattern_risk_bonus") or 0)
        if bonus:
            rs = int(risk_result.get("risk_score") or 0) + bonus
            risk_result["risk_score"] = min(rs, 100)
            note = sess.get("pattern_note")
            if note:
                risks.append(note)
        risk_result["risks_identified"] = list(dict.fromkeys(risks))

        if manual == "force_allow":
            risk_result["risk_score"] = min(int(risk_result.get("risk_score") or 0), 18)
            r2 = list(risk_result.get("risks_identified") or [])
            r2.append("Operator override: permit access (audited).")
            risk_result["risks_identified"] = list(dict.fromkeys(r2))
        elif manual == "force_block":
            risk_result["risk_score"] = max(int(risk_result.get("risk_score") or 0), 88)
            r2 = list(risk_result.get("risks_identified") or [])
            r2.append("Operator override: block access (audited).")
            risk_result["risks_identified"] = list(dict.fromkeys(r2))
        elif manual == "force_review":
            risk_result["risk_score"] = max(int(risk_result.get("risk_score") or 0), 42)
            r2 = list(risk_result.get("risks_identified") or [])
            r2.append("Operator override: require human review (audited).")
            risk_result["risks_identified"] = list(dict.fromkeys(r2))

        if llm_result and llm_result.get("note"):
            r2 = list(risk_result.get("risks_identified") or [])
            r2.append(llm_result["note"])
            risk_result["risks_identified"] = list(dict.fromkeys(r2))

        meta = {
            "status": evaluation_status,
            "attack_categories": categories,
            "llm_guard_used": bool(llm_result),
            "regex_matched": bool(layers.get("regex_matched")),
            "high_tier_regex": bool(layers.get("high_tier_matched")),
            "suspicious_structure": bool(layers.get("suspicious_structure")),
            "session": sess,
            "manual_override": manual,
            "detector": {
                "review_required": bool(layers.get("review_required")),
                "semantic_uncertain": bool(layers.get("semantic_uncertain")),
            },
        }

        return {
            "agent_used": agent.__class__.__name__,
            "agent_output": agent_output,
            "policy": policy_result,
            "risk": risk_result,
            "meta": meta,
        }
