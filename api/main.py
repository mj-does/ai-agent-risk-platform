from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import traceback
from datetime import datetime
import uuid

from fastapi.middleware.cors import CORSMiddleware

# import router
from agents.router import Router

# 🔥 TIGERGRAPH IMPORTS (CLEANED — NO DUPLICATES)
from backend.tiger_client import (
    insert_prompt,
    get_prompts,
    insert_agent,
    insert_tool,
    insert_action,
    insert_system,
    insert_edge_prompt_agent,
    insert_edge_agent_tool,
    insert_edge_tool_action,
    insert_edge_action_system
)

app = FastAPI(
    title="AI Agent Risk Platform",
    description="API to analyze AI agent risk",
    version="1.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# initialize router
router = Router()


# request schema
class PromptRequest(BaseModel):
    prompt: str
    agent_name: str
    industry: str
    use_case: str


@app.get("/")
def root():
    return {"message": "AI Agent Risk Platform running"}


@app.post("/analyze")
def analyze_prompt(request: PromptRequest):
    try:
        payload = {
            "prompt": request.prompt,
            "agent_name": request.agent_name,
            "industry": request.industry,
            "use_case": request.use_case
        }

        # 🔥 RUN YOUR EXISTING PIPELINE
        result = router.run(payload)

        # =========================
        # 🔥 TIGERGRAPH INTEGRATION
        # =========================

        timestamp = datetime.utcnow().isoformat()

        # generate IDs
        prompt_id = str(uuid.uuid4())
        agent_id = "agent_" + request.agent_name.replace(" ", "_")
        tool_id = "tool_llm"
        action_id = "action_analysis"
        system_id = "system_backend"

        risk_score = result.get("risk_score", 0)
        intent = result.get("intent", "unknown")

        # VERTICES
        insert_prompt(None, {
            "prompt_id": prompt_id,
            "text": request.prompt,
            "risk_score": risk_score,
            "intent": intent,
            "timestamp": timestamp,
            "status": "blocked" if risk_score > 7 else "allowed"
        })

        insert_agent(None, {
            "agent_id": agent_id,
            "agent_name": request.agent_name,
            "agent_type": "AI"
        })

        insert_tool(None, {
            "tool_id": tool_id,
            "tool_name": "LLM",
            "risk_level": "medium"
        })

        insert_action(None, {
            "action_id": action_id,
            "action_name": "analyze_prompt",
            "severity": "medium"
        })

        insert_system(None, {
            "system_id": system_id,
            "system_name": "backend",
            "criticality": "high"
        })

        # EDGES
        insert_edge_prompt_agent(None, prompt_id, agent_id, True)
        insert_edge_agent_tool(None, agent_id, tool_id, timestamp)
        insert_edge_tool_action(None, tool_id, action_id, timestamp)
        insert_edge_action_system(None, action_id, system_id, risk_score)

        # =========================

        return {
            "status": "success",
            "data": result,
            "graph_logged": True
        }

    except Exception as e:
        print("ERROR OCCURRED:")
        print(traceback.format_exc())

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )