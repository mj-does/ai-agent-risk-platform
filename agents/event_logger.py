import json
from datetime import datetime

def log_event(prompt, risk, agent, decision):
    event = {
        "timestamp": str(datetime.now()),
        "prompt": prompt,
        "risk_score": risk,
        "agent": agent,
        "decision": decision
    }

    with open("agent_logs.json", "a") as f:
        f.write(json.dumps(event) + "\n")
# Logger for tracking agent events
class EventLogger:
    pass
