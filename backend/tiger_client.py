import requests
import os
from dotenv import load_dotenv

load_dotenv()

TG_HOST = os.getenv("TG_HOST")
TG_TOKEN = os.getenv("TG_TOKEN")
TG_GRAPH = os.getenv("TG_GRAPH")

def _normalize_host(host: str) -> str:
    h = (host or "").strip().rstrip("/")
    return h

# TigerGraph Cloud RESTPP is typically served over HTTPS (443) at:
#   https://<tgcloud-host>/restpp/graph/<graphName>
# Self-managed installs often use :14240, but hardcoding that breaks cloud deployments.
HOST = _normalize_host(TG_HOST)
BASE_URL = f"{HOST}/restpp/graph/{TG_GRAPH}" if HOST and TG_GRAPH else ""

HEADERS = {
    "Authorization": f"Bearer {TG_TOKEN}",
    "Content-Type": "application/json"
}


def _post(payload):
    url = BASE_URL

    print("\n========== TIGERGRAPH REQUEST ==========")
    print("URL:", url)
    print("PAYLOAD:", payload)
    print("========================================\n")

    try:
        if not url:
            return {"error": "TigerGraph not configured (missing TG_HOST/TG_GRAPH)"}

        # ⏱️ HARD TIMEOUT (KEY FIX)
        response = requests.post(
            url,
            headers=HEADERS,
            json=payload,
            timeout=5   # force fast fail
        )

        print("Response Status:", response.status_code)
        print("Response Body:", response.text)

        return response.json()

    except requests.exceptions.Timeout:
        print("❌ TigerGraph TIMEOUT (network / cloud slow)")
        return {"error": "timeout"}

    except Exception as e:
        print("❌ TigerGraph ERROR:", str(e))
        return {"error": str(e)}


# =========================
# VERTICES
# =========================

def insert_prompt(_, data):
    return _post({
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
    })


def insert_agent(_, data):
    return _post({
        "vertices": {
            "Agent": {
                data["agent_id"]: {
                    "agent_name": {"value": data["agent_name"]},
                    "agent_type": {"value": data["agent_type"]}
                }
            }
        }
    })


def insert_tool(_, data):
    return _post({
        "vertices": {
            "Tool": {
                data["tool_id"]: {
                    "tool_name": {"value": data["tool_name"]},
                    "risk_level": {"value": float(data["risk_level"])}
                }
            }
        }
    })


def insert_action(_, data):
    return _post({
        "vertices": {
            "Action": {
                data["action_id"]: {
                    "action_name": {"value": data["action_name"]},
                    "severity": {"value": float(data["severity"])}
                }
            }
        }
    })


def insert_system(_, data):
    return _post({
        "vertices": {
            "System": {
                data["system_id"]: {
                    "system_name": {"value": data["system_name"]},
                    "criticality": {"value": float(data["criticality"])}
                }
            }
        }
    })


# =========================
# EDGES
# =========================

def insert_edge_prompt_agent(_, prompt_id, agent_id, success):
    return _post({
        "edges": {
            "Prompt": {
                prompt_id: {
                    "PROMPT_TRIGGERS_AGENT": {
                        "Agent": {
                            agent_id: {
                                "risk_passed": {"value": 1.0 if success else 0.0}
                            }
                        }
                    }
                }
            }
        }
    })


def insert_edge_agent_tool(_, agent_id, tool_id, timestamp):
    return _post({
        "edges": {
            "Agent": {
                agent_id: {
                    "AGENT_USES_TOOL": {
                        "Tool": {
                            tool_id: {
                                "timestamp": {"value": timestamp}
                            }
                        }
                    }
                }
            }
        }
    })


def insert_edge_tool_action(_, tool_id, action_id, timestamp):
    return _post({
        "edges": {
            "Tool": {
                tool_id: {
                    "TOOL_EXECUTES_ACTION": {
                        "Action": {
                            action_id: {
                                "timestamp": {"value": timestamp}
                            }
                        }
                    }
                }
            }
        }
    })


def insert_edge_action_system(_, action_id, system_id, risk_score):
    return _post({
        "edges": {
            "Action": {
                action_id: {
                    "ACTION_AFFECTS_SYSTEM": {
                        "System": {
                            system_id: {
                                "impact_score": {"value": float(risk_score)}
                            }
                        }
                    }
                }
            }
        }
    })


def get_prompts():
    url = f"{BASE_URL}/vertices/Prompt"
    response = requests.get(url, headers=HEADERS, timeout=5)
    return response.json()