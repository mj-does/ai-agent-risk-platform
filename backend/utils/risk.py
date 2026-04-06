def compute_risk(prompt: str, intent: str, injection_flag: bool) -> float:
    risk = 0.0
    
    # Rule-based injection found
    if injection_flag:
        risk += 0.7
        
    # Risky intents assigned by the LLM
    high_risk_intents = ["delete_resource", "execute_code", "privilege_escalation"]
    moderate_risk_intents = ["write_data", "read_data"]
    
    if intent in high_risk_intents:
        risk += 0.6
    elif intent in moderate_risk_intents:
        risk += 0.3
    elif intent == "unknown":
        risk += 0.2
        
    # Ensure risk score stays between 0 and 1
    return round(min(1.0, risk), 2)

def risk_label(score):
    if score > 0.8:
        return "HIGH"
    elif score > 0.5:
        return "MEDIUM"
    return "LOW"
