from backend.tiger_client import (
    insert_prompt,
    insert_agent,
    insert_tool,
    insert_action,
    insert_system,
    insert_edge_prompt_agent,
    insert_edge_agent_tool,
    insert_edge_tool_action,
    insert_edge_action_system,
)


def log_to_graph(data):
    conn = None

    # VERTICES
    insert_prompt(conn, {
        "prompt_id": data["prompt_id"],
        "text": data["text"],
        "risk_score": data["risk_score"],
        "intent": data["intent"],
        "timestamp": data["timestamp"],
        "status": data["status"]
    })

    insert_agent(conn, {
        "agent_id": data["agent_id"],
        "agent_name": data["agent_name"],
        "agent_type": data["agent_type"]
    })

    insert_tool(conn, {
        "tool_id": data["tool_id"],
        "tool_name": data["tool_name"],
        "risk_level": data["tool_risk"]
    })

    insert_action(conn, {
        "action_id": data["action_id"],
        "action_name": data["action_name"],
        "severity": data["severity"]
    })

    insert_system(conn, {
        "system_id": data["system_id"],
        "system_name": data["system_name"],
        "criticality": data["criticality"]
    })

    # EDGES
    insert_edge_prompt_agent(conn, data["prompt_id"], data["agent_id"], True)

    insert_edge_agent_tool(conn, data["agent_id"], data["tool_id"], data["timestamp"])

    insert_edge_tool_action(conn, data["tool_id"], data["action_id"], data["timestamp"])

    insert_edge_action_system(conn, data["action_id"], data["system_id"], data["impact_score"])