from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models import EventPayload, ExecutionRequest
from tiger_client import (
    get_conn,
    insert_prompt, insert_agent, insert_tool,
    insert_action, insert_system,
    insert_edge_prompt_agent, insert_edge_agent_tool,
    insert_edge_tool_action, insert_edge_action_system
)
from datetime import datetime

app = FastAPI(title="Graph & Backend Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

conn = get_conn()

@app.post("/log_event")
async def log_event(payload: EventPayload):
    ts = payload.timestamp or datetime.utcnow().isoformat()

    if payload.event_type == "prompt_received":
        insert_prompt(conn, {
            "prompt_id":  payload.prompt_id,
            "text":       payload.prompt_text,
            "risk_score": payload.risk_score,
            "intent":     payload.intent,
            "timestamp":  ts,
            "status":     "pending"
        })

    elif payload.event_type == "agent_selected":
        insert_agent(conn, {
            "agent_id":   payload.agent_id,
            "agent_name": payload.agent_name,
            "agent_type": payload.agent_type
        })
        insert_edge_prompt_agent(conn, payload.prompt_id, payload.agent_id, payload.risk_score)

    elif payload.event_type == "tool_called":
        insert_tool(conn, {
            "tool_id":    payload.tool_id,
            "tool_name":  payload.tool_name,
            "risk_level": payload.tool_risk
        })
        insert_edge_agent_tool(conn, payload.agent_id, payload.tool_id, ts)

    elif payload.event_type == "action_selected":
        insert_action(conn, {
            "action_id":   payload.action_id,
            "action_name": payload.action_name,
            "severity":    payload.action_severity
        })
        insert_edge_tool_action(conn, payload.tool_id, payload.action_id, ts)

    elif payload.event_type == "target_system":
        insert_system(conn, {
            "system_id":   payload.system_id,
            "system_name": payload.system_name,
            "criticality": payload.system_criticality
        })
        insert_edge_action_system(conn, payload.action_id, payload.system_id, payload.action_severity * payload.system_criticality)

    return {"status": "logged", "event_type": payload.event_type}


@app.post("/should_execute")
async def should_execute(req: ExecutionRequest):
    try:
        results = conn.runInstalledQuery("risk_propagation", {"prompt_id": req.prompt_id})
        propagated_risk = results[0].get("propagated_risk", 0.0)
        affected_systems = results[0].get("affected_systems", [])
    except:
        propagated_risk = 0.0
        affected_systems = []

    if propagated_risk > 0.8:
        decision = "block"
        reason = "Risk score too high — action blocked"
    elif propagated_risk > 0.6:
        decision = "warn"
        reason = "High risk — proceed with caution"
    elif propagated_risk > 0.3:
        decision = "approve_required"
        reason = "Moderate risk — manual approval needed"
    else:
        decision = "allow"
        reason = "Low risk — execution permitted"

    return {
        "decision":         decision,
        "propagated_risk":  propagated_risk,
        "affected_systems": affected_systems,
        "reason":           reason
    }


@app.get("/graph_status")
async def graph_status():
    from tiger_client import get_vertices
    prompts = get_vertices("Prompt")
    agents  = get_vertices("Agent")
    tools   = get_vertices("Tool")
    actions = get_vertices("Action")
    systems = get_vertices("System")

    return {
        "nodes": {
            "prompts": prompts,
            "agents":  agents,
            "tools":   tools,
            "actions": actions,
            "systems": systems
        },
        "counts": {
            "prompts": len(prompts),
            "agents":  len(agents),
            "tools":   len(tools),
            "actions": len(actions),
            "systems": len(systems)
        }
    }
