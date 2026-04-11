from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import traceback
from datetime import datetime
import uuid
import os

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
    session_id: Optional[str] = None
    manual_override: Optional[str] = None  # force_allow | force_block | force_review


@app.get("/")
def root():
    return {"message": "AI Agent Risk Platform running"}


@app.get("/integrations")
def integrations_status():
    """
    Quick check of optional integrations (no secrets exposed).
    TigerGraph is active only when all three env vars are set; graph_logged on /analyze
    confirms REST calls succeeded.
    """
    tg_ready = bool(
        os.getenv("TG_HOST") and os.getenv("TG_TOKEN") and os.getenv("TG_GRAPH")
    )
    llm_ready = bool(os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY"))
    return {
        "tigergraph_configured": tg_ready,
        "llm_guard_configured": llm_ready,
        "llm_semantic_fallback_env": (os.getenv("LLM_SEMANTIC_FALLBACK") or "default:on"),
    }


@app.post("/analyze")
def analyze_prompt(request: PromptRequest):
    try:
        payload = {
            "prompt": request.prompt,
            "agent_name": request.agent_name,
            "industry": request.industry,
            "use_case": request.use_case,
            "session_id": request.session_id,
            "manual_override": request.manual_override,
        }

        # 🔥 RUN YOUR EXISTING PIPELINE
        result = router.run(payload)

        # -------------------------
        # Normalize output for UI
        # -------------------------
        risk_obj = (result or {}).get("risk", {}) or {}
        policy_obj = (result or {}).get("policy", {}) or {}
        agent_used = (result or {}).get("agent_used", "unknown")
        meta = (result or {}).get("meta") or {}

        # `risk_engine.score_risk` produces a point score (commonly 0–100+).
        # For consistent UI + graph logging, expose 0–10 and 0–1 scales.
        risk_points = risk_obj.get("risk_score", 0) or 0
        try:
            risk_points = float(risk_points)
        except Exception:
            risk_points = 0.0

        risk_0_10 = max(0.0, min(10.0, round(risk_points / 10.0, 2)))
        risk_0_1 = max(0.0, min(1.0, round(risk_0_10 / 10.0, 4)))

        analysis = {
            "risk_score": risk_0_10,  # 0–10 (legacy-friendly)
            "risk_score_normalized": risk_0_1,  # 0–1 (frontend-friendly)
            "risk_level": risk_obj.get("risk_level", "UNKNOWN"),
            "risks_identified": risk_obj.get("risks_identified", []) or [],
            "policy": policy_obj,
            "agent_used": agent_used,
            "prompt_id": None,
            "status": meta.get("status") or "clear",
            "attack_categories": meta.get("attack_categories") or [],
            "llm_guard_used": bool(meta.get("llm_guard_used")),
            "regex_matched": meta.get("regex_matched"),
            "suspicious_structure": meta.get("suspicious_structure"),
            "session": meta.get("session"),
            "manual_override": meta.get("manual_override"),
        }

        # =========================
        # 🔥 TIGERGRAPH INTEGRATION
        # =========================

        graph_logged = False
        timestamp = datetime.utcnow().isoformat()

        # generate IDs
        prompt_id = str(uuid.uuid4())
        agent_id = "agent_" + request.agent_name.replace(" ", "_")
        tool_id = "tool_llm"
        action_id = "action_analysis"
        system_id = "system_backend"

        risk_score = risk_0_10
        intent = "unknown"

        # expose prompt_id for frontend / audit trail regardless of TG logging outcome
        analysis["prompt_id"] = prompt_id

        # If TigerGraph isn't configured, skip logging so /analyze stays fast.
        tg_ready = bool(os.getenv("TG_HOST") and os.getenv("TG_TOKEN") and os.getenv("TG_GRAPH"))
        if tg_ready:
            try:
                def _ok(resp):
                    # backend.tiger_client returns {"error": "..."} on failures
                    return not (isinstance(resp, dict) and resp.get("error"))

                # VERTICES
                r1 = insert_prompt(None, {
                    "prompt_id": prompt_id,
                    "text": request.prompt,
                    "risk_score": risk_score,
                    "intent": intent,
                    "timestamp": timestamp,
                    "status": "blocked" if risk_score > 7 else "allowed"
                })

                r2 = insert_agent(None, {
                    "agent_id": agent_id,
                    "agent_name": request.agent_name,
                    "agent_type": "AI"
                })

                r3 = insert_tool(None, {
                    "tool_id": tool_id,
                    "tool_name": "LLM",
                    "risk_level": 0.6
                })

                r4 = insert_action(None, {
                    "action_id": action_id,
                    "action_name": "analyze_prompt",
                    "severity": 0.4
                })

                r5 = insert_system(None, {
                    "system_id": system_id,
                    "system_name": "backend",
                    "criticality": 0.8
                })

                # EDGES
                r6 = insert_edge_prompt_agent(None, prompt_id, agent_id, True)
                r7 = insert_edge_agent_tool(None, agent_id, tool_id, timestamp)
                r8 = insert_edge_tool_action(None, tool_id, action_id, timestamp)
                r9 = insert_edge_action_system(None, action_id, system_id, risk_score)

                graph_logged = all(_ok(r) for r in [r1, r2, r3, r4, r5, r6, r7, r8, r9])
            except Exception as _e:
                graph_logged = False

        # =========================

        return {
            "status": "success",
            "analysis": analysis,
            "data": result,  # raw pipeline output (useful for debugging)
            "graph_logged": graph_logged,
            "prompt_id": prompt_id,
        }

    except Exception as e:
        print("ERROR OCCURRED:")
        print(traceback.format_exc())

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )