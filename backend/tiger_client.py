import requests
import os
from dotenv import load_dotenv

load_dotenv()

TG_HOST = os.getenv("TG_HOST")
TG_TOKEN = os.getenv("TG_TOKEN")
TG_GRAPH = os.getenv("TG_GRAPH")

HEADERS = {
    "Authorization": f"Bearer {TG_TOKEN}",
    "Content-Type": "application/json"
}

# =========================
# GENERIC HELPER
# =========================
def _post(payload):
    url = f"{TG_HOST}/graph/{TG_GRAPH}"
    
    # 🔥 LOGGING FOR DEMO PROOF
    print("\n========== TIGERGRAPH REQUEST ==========")
    print("URL:", url)
    print("PAYLOAD:", payload)
    print("========================================\n")

    try:
        response = requests.post(url, headers=HEADERS, json=payload, timeout=5)
        print("Response Status:", response.status_code)
        print("Response Body:", response.text)
        return response.json()
    except Exception as e:
        print("TigerGraph ERROR:", str(e))
        return {"error": str(e)}


# =========================
# VERTEX INSERTS
# =========================

def insert_prompt(_, data):
    payload = {
        "vertices": {
            "Prompt": {
                data["prompt_id"]: {
                    "text": {"value": data["text"]},
                    "risk_score": {"value": data["risk_score"]},
                    "intent": {"value": data["intent"]},
                    "timestamp": {"value": data["timestamp"]},
                    "status": {"value": data["status"]}
                }
            }
        }
    }
    return _post(payload)


def insert_agent(_, data):
    payload = {
        "vertices": {
            "Agent": {
                data["agent_id"]: {
                    "agent_name": {"value": data["agent_name"]},
                    "agent_type": {"value": data["agent_type"]}
                }
            }
        }
    }
    return _post(payload)


def insert_tool(_, data):
    payload = {
        "vertices": {
            "Tool": {
                data["tool_id"]: {
                    "tool_name": {"value": data["tool_name"]},
                    "risk_level": {"value": data["risk_level"]}
                }
            }
        }
    }
    return _post(payload)


def insert_action(_, data):
    payload = {
        "vertices": {
            "Action": {
                data["action_id"]: {
                    "action_name": {"value": data["action_name"]},
                    "severity": {"value": data["severity"]}
                }
            }
        }
    }
    return _post(payload)


def insert_system(_, data):
    payload = {
        "vertices": {
            "System": {
                data["system_id"]: {
                    "system_name": {"value": data["system_name"]},
                    "criticality": {"value": data["criticality"]}
                }
            }
        }
    }
    return _post(payload)


# =========================
# EDGE INSERTS
# =========================

def insert_edge_prompt_agent(_, prompt_id, agent_id, success):
    payload = {
        "edges": {
            "Prompt": {
                prompt_id: {
                    "used_by": {
                        "Agent": {
                            agent_id: {
                                "success": {"value": success}
                            }
                        }
                    }
                }
            }
        }
    }
    return _post(payload)


def insert_edge_agent_tool(_, agent_id, tool_id, timestamp):
    payload = {
        "edges": {
            "Agent": {
                agent_id: {
                    "uses": {
                        "Tool": {
                            tool_id: {
                                "timestamp": {"value": timestamp}
                            }
                        }
                    }
                }
            }
        }
    }
    return _post(payload)


def insert_edge_tool_action(_, tool_id, action_id, timestamp):
    payload = {
        "edges": {
            "Tool": {
                tool_id: {
                    "triggers": {
                        "Action": {
                            action_id: {
                                "timestamp": {"value": timestamp}
                            }
                        }
                    }
                }
            }
        }
    }
    return _post(payload)


def insert_edge_action_system(_, action_id, system_id, risk_score):
    payload = {
        "edges": {
            "Action": {
                action_id: {
                    "affects": {
                        "System": {
                            system_id: {
                                "risk_score": {"value": risk_score}
                            }
                        }
                    }
                }
            }
        }
    }
    return _post(payload)


# =========================
# FETCH
# =========================

def get_prompts():
    url = f"{TG_HOST}/graph/{TG_GRAPH}/vertices/Prompt"
    response = requests.get(url, headers=HEADERS)
    return response.json()