import requests
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("TG_HOST")
GRAPH = os.getenv("TG_GRAPHNAME")
USERNAME = os.getenv("TG_USERNAME")
PASSWORD = os.getenv("TG_PASSWORD")
SECRET = os.getenv("TG_SECRET")

def get_token():
    url = f"{BASE_URL}/gsql/v1/tokens"
    r = requests.post(url, json={"secret": SECRET})
    if r.status_code == 200:
        return r.json().get("token", "")
    return None
def get_headers():
    token = get_token()
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}

def upsert(vertex_type, vertex_id, attrs):
    headers = get_headers()
    url = f"{BASE_URL}/restpp/graph/{GRAPH}"
    payload = {
        "vertices": {
            vertex_type: {
                vertex_id: {k: {"value": v} for k, v in attrs.items()}
            }
        }
    }
    r = requests.post(url, json=payload, headers=headers)
    return r.json()

def upsert_edge(from_type, from_id, edge_type, to_type, to_id, attrs):
    headers = get_headers()
    url = f"{BASE_URL}/restpp/graph/{GRAPH}"
    payload = {
        "edges": {
            from_type: {
                from_id: {
                    edge_type: {
                        to_type: {
                            to_id: {k: {"value": v} for k, v in attrs.items()}
                        }
                    }
                }
            }
        }
    }
    r = requests.post(url, json=payload, headers=headers)
    return r.json()

def get_conn():
    return None  # Not needed anymore

def insert_prompt(conn, data):
    upsert("Prompt", data["prompt_id"], {
        "text": data["text"],
        "risk_score": data["risk_score"],
        "intent": data["intent"],
        "timestamp": data["timestamp"],
        "status": data["status"]
    })

def insert_agent(conn, data):
    upsert("Agent", data["agent_id"], {
        "agent_name": data["agent_name"],
        "agent_type": data["agent_type"]
    })

def insert_tool(conn, data):
    upsert("Tool", data["tool_id"], {
        "tool_name": data["tool_name"],
        "risk_level": data["risk_level"]
    })

def insert_action(conn, data):
    upsert("Action", data["action_id"], {
        "action_name": data["action_name"],
        "severity": data["severity"]
    })

def insert_system(conn, data):
    upsert("System", data["system_id"], {
        "system_name": data["system_name"],
        "criticality": data["criticality"]
    })

def insert_edge_prompt_agent(conn, prompt_id, agent_id, risk_passed):
    upsert_edge("Prompt", prompt_id, "PROMPT_TRIGGERS_AGENT", "Agent", agent_id, {"risk_passed": risk_passed})

def insert_edge_agent_tool(conn, agent_id, tool_id, timestamp):
    upsert_edge("Agent", agent_id, "AGENT_USES_TOOL", "Tool", tool_id, {"timestamp": timestamp})

def insert_edge_tool_action(conn, tool_id, action_id, timestamp):
    upsert_edge("Tool", tool_id, "TOOL_EXECUTES_ACTION", "Action", action_id, {"timestamp": timestamp})

def insert_edge_action_system(conn, action_id, system_id, impact_score):
    upsert_edge("Action", action_id, "ACTION_AFFECTS_SYSTEM", "System", system_id, {"impact_score": impact_score})
def get_vertices(vertex_type):
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    url = f"{BASE_URL}/restpp/graph/{GRAPH}/vertices/{vertex_type}"
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        return r.json().get("results", [])
    return []
