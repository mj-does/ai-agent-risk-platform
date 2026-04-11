from typing import Optional, List

from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel, Field
import traceback
from datetime import datetime
import uuid
import os
import secrets
import threading

from fastapi.middleware.cors import CORSMiddleware

# import router
from agents.router import Router

# 🔥 TIGERGRAPH IMPORTS (CLEANED — NO DUPLICATES)
from backend.tiger_client import (
    insert_prompt,
    get_prompts,
    insert_user,
    insert_session,
    insert_policy_rule,
    insert_dataclass,
    insert_agent,
    insert_model_provider,
    insert_tool,
    insert_action,
    insert_system,
    insert_control,
    insert_ticket,
    insert_approval,
    insert_edge_user_session,
    insert_edge_session_prompt,
    insert_edge_policy_prompt,
    insert_edge_dataclass_system,
    insert_edge_agent_model,
    insert_edge_model_tool,
    insert_edge_agent_tool,
    insert_edge_tool_action,
    insert_edge_action_system,
    insert_edge_action_mitigated,
    insert_edge_prompt_ticket,
    insert_edge_ticket_approval,
    insert_edge_prompt_agent_legacy,
    insert_edge_agent_tool_legacy,
    insert_edge_tool_action_legacy,
    insert_edge_action_system_legacy,
    query_risk_propagation,
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

# --- In-memory admin escalation queue (hackathon / demo — not durable) ---
_escalation_lock = threading.Lock()
_escalations: List[dict] = []


def _admin_expected_credentials():
    admin_id = (os.getenv("ADMIN_ID") or "admin").strip()
    admin_pw = (os.getenv("ADMIN_PASSWORD") or "changeme").strip()
    return admin_id, admin_pw


def _verify_admin_credentials(admin_id: str, admin_password: str) -> bool:
    expected_id, expected_pw = _admin_expected_credentials()
    if not expected_pw:
        return False
    a = (admin_id or "").strip()
    p = (admin_password or "").strip()
    return secrets.compare_digest(a, expected_id) and secrets.compare_digest(
        p, expected_pw
    )


# request schema
class PromptRequest(BaseModel):
    prompt: str
    agent_name: str
    industry: str
    use_case: str
    session_id: Optional[str] = None
    manual_override: Optional[str] = None  # force_allow | force_block | force_review


class AdminVerifyRequest(BaseModel):
    admin_id: str = Field(..., min_length=1)
    admin_password: str = Field(..., min_length=1)


class EscalationCreate(BaseModel):
    prompt: str = Field(..., min_length=1)
    prompt_id: Optional[str] = None
    session_id: Optional[str] = None
    risk_score_normalized: Optional[float] = None
    risk_level: Optional[str] = None
    decision: Optional[str] = None


@app.get("/")
def root():
    return {"message": "AI Agent Risk Platform running"}


@app.get("/graph/risk_propagation")
def graph_risk_propagation_check(prompt_id: str):
    """
    Server-side TigerGraph check for a Prompt id (same logic as /analyze after insert).
    Example: GET /graph/risk_propagation?prompt_id=<uuid>
    """
    qp = query_risk_propagation(prompt_id)
    return {"prompt_id": prompt_id, **qp}


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


@app.post("/admin/verify")
def admin_verify(req: AdminVerifyRequest):
    """
    Verify demo admin credentials (ADMIN_ID / ADMIN_PASSWORD in env).
    Used by the UI before re-submitting a blocked prompt with force_allow.
    """
    ok = _verify_admin_credentials(req.admin_id, req.admin_password)
    return {"ok": ok}


@app.post("/admin/escalation_requests")
def create_escalation_request(req: EscalationCreate):
    """Queue a blocked prompt for admin review (in-memory; demo only)."""
    rid = str(uuid.uuid4())
    row = {
        "id": rid,
        "prompt": req.prompt,
        "prompt_id": req.prompt_id,
        "session_id": req.session_id,
        "risk_score_normalized": req.risk_score_normalized,
        "risk_level": req.risk_level,
        "decision": req.decision,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat() + "Z",
    }
    with _escalation_lock:
        _escalations.insert(0, row)
        _escalations[:] = _escalations[:200]
    return {"status": "queued", "request": row}


@app.get("/admin/escalation_requests")
def list_escalation_requests(
    x_admin_password: Optional[str] = Header(None, alias="X-Admin-Password"),
):
    """
    List queued escalation requests. For the hackathon demo, protect with
    X-Admin-Password matching ADMIN_PASSWORD (same as admin login).
    """
    _, expected_pw = _admin_expected_credentials()
    if expected_pw and not secrets.compare_digest(
        (x_admin_password or "").strip(), expected_pw
    ):
        raise HTTPException(status_code=401, detail="Admin password required")
    with _escalation_lock:
        return {"requests": list(_escalations)}


@app.delete("/admin/escalation_requests/{request_id}")
def dismiss_escalation_request(
    request_id: str,
    x_admin_password: Optional[str] = Header(None, alias="X-Admin-Password"),
):
    _, expected_pw = _admin_expected_credentials()
    if expected_pw and not secrets.compare_digest(
        (x_admin_password or "").strip(), expected_pw
    ):
        raise HTTPException(status_code=401, detail="Admin password required")
    with _escalation_lock:
        before = len(_escalations)
        _escalations[:] = [r for r in _escalations if r.get("id") != request_id]
        removed = before - len(_escalations)
    return {"removed": removed}


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

        # generate IDs — extended graph: identity, session, policy/data class, model path + fan-out tools
        prompt_id = str(uuid.uuid4())
        session_id = (request.session_id or "").strip() or str(uuid.uuid4())
        user_id = "user_demo"
        agent_id = "agent_" + request.agent_name.replace(" ", "_")
        rule_id = "rule_default"
        class_id = "dc_internal"
        provider_id = "provider_primary"
        tool_llm_id = "tool_llm"
        tool_retrieval_id = "tool_retrieval_direct"
        action_analyze_id = "action_analyze"
        action_fetch_id = "action_fetch"
        system_api_id = "system_api"
        system_db_id = "system_db"
        control_id = "control_dlp"

        risk_score = risk_0_10
        intent = "unknown"
        industry_l = (request.industry or "").lower()
        sensitivity = "PCI" if "finance" in industry_l or "payment" in industry_l else (
            "PII" if "health" in industry_l or "hr" in industry_l else "internal"
        )
        session_risk = min(1.0, max(0.0, risk_0_1 * 1.2))

        # expose prompt_id for frontend / audit trail regardless of TG logging outcome
        analysis["prompt_id"] = prompt_id

        # If TigerGraph isn't configured, skip logging so /analyze stays fast.
        tg_ready = bool(os.getenv("TG_HOST") and os.getenv("TG_TOKEN") and os.getenv("TG_GRAPH"))
        if tg_ready:
            def _ok(resp):
                # backend.tiger_client returns {"error": "..."} on failures
                return not (isinstance(resp, dict) and resp.get("error"))

            try:
                # --- Phase A: minimal connected chain (Prompt→Agent→Tool→Action→System) ---
                # Uses legacy edge payloads (fewer attrs) so older TG schemas still link.
                # Previously, extended types (User, ModelProvider, …) could fail first while
                # Prompt still upserted — leaving an orphan vertex in GraphStudio.
                core = [
                    insert_prompt(None, {
                        "prompt_id": prompt_id,
                        "text": request.prompt,
                        "risk_score": risk_score,
                        "intent": intent,
                        "timestamp": timestamp,
                        "status": "blocked" if risk_score > 7 else "allowed"
                    }),
                    insert_agent(None, {
                        "agent_id": agent_id,
                        "agent_name": request.agent_name,
                        "agent_type": "AI"
                    }),
                    insert_tool(None, {
                        "tool_id": tool_llm_id,
                        "tool_name": "LLM_completion",
                        "risk_level": 0.6
                    }),
                    insert_action(None, {
                        "action_id": action_analyze_id,
                        "action_name": "analyze_prompt",
                        "severity": 0.4
                    }),
                    insert_system(None, {
                        "system_id": system_api_id,
                        "system_name": "api_core",
                        "criticality": 0.85
                    }),
                    insert_edge_prompt_agent_legacy(None, prompt_id, agent_id, 1.0),
                    insert_edge_agent_tool_legacy(None, agent_id, tool_llm_id, timestamp),
                    insert_edge_tool_action_legacy(None, tool_llm_id, action_analyze_id, timestamp),
                    insert_edge_action_system_legacy(None, action_analyze_id, system_api_id, risk_score),
                ]
                graph_logged = all(_ok(r) for r in core)
            except Exception:
                graph_logged = False

            try:
                # --- Phase B: extended graph (best effort; never affects graph_logged) ---
                insert_user(None, {"user_id": user_id, "email": "", "role": "user"})
                insert_session(
                    None,
                    {"session_id": session_id, "label": "web", "session_risk": session_risk},
                )
                insert_policy_rule(
                    None,
                    {
                        "rule_id": rule_id,
                        "rule_name": "default_policy",
                        "sensitivity": sensitivity,
                    },
                )
                insert_dataclass(
                    None,
                    {
                        "class_id": class_id,
                        "label": sensitivity,
                        "tier": 2.0 if sensitivity != "internal" else 1.0,
                    },
                )
                insert_model_provider(
                    None,
                    {
                        "provider_id": provider_id,
                        "vendor": agent_used or "llm",
                        "model_name": "primary",
                    },
                )
                insert_tool(None, {
                    "tool_id": tool_retrieval_id,
                    "tool_name": "retrieval_connector",
                    "risk_level": 0.45
                })
                insert_action(None, {
                    "action_id": action_fetch_id,
                    "action_name": "fetch_context",
                    "severity": 0.35
                })
                insert_system(None, {
                    "system_id": system_db_id,
                    "system_name": "data_warehouse",
                    "criticality": 0.75
                })
                insert_control(
                    None,
                    {
                        "control_id": control_id,
                        "name": "DLP_screening",
                        "effectiveness": 0.35,
                    },
                )
                insert_edge_user_session(
                    None, user_id, session_id,
                    confidence=0.99, observed_at=timestamp, revoked=0,
                )
                insert_edge_session_prompt(
                    None, session_id, prompt_id,
                    confidence=0.97, observed_at=timestamp, revoked=0,
                )
                insert_edge_policy_prompt(
                    None, rule_id, prompt_id, severity_weight=1.0 if sensitivity == "internal" else 1.15
                )
                insert_edge_dataclass_system(None, class_id, system_api_id, coverage=0.9)
                insert_edge_dataclass_system(None, class_id, system_db_id, coverage=0.85)
                insert_edge_agent_model(
                    None, agent_id, provider_id,
                    confidence=0.98, observed_at=timestamp, revoked=0,
                )
                insert_edge_model_tool(
                    None, provider_id, tool_llm_id,
                    weight=0.9, observed_at=timestamp, revoked=0,
                )
                insert_edge_agent_tool(
                    None, agent_id, tool_retrieval_id, timestamp,
                    confidence=0.82, observed_at=timestamp, revoked=0,
                )
                insert_edge_tool_action(
                    None, tool_retrieval_id, action_fetch_id, timestamp,
                    weight=0.88, observed_at=timestamp, revoked=0,
                )
                insert_edge_action_mitigated(
                    None, action_analyze_id, control_id,
                    mitigated_at=timestamp, confidence=0.88,
                )
                insert_edge_action_system(
                    None, action_fetch_id, system_db_id, risk_score * 0.85,
                    observed_at=timestamp, revoked=0,
                )
                if risk_score > 7:
                    ticket_id = f"ticket_{prompt_id[:8]}"
                    approval_id = f"appr_{prompt_id[:8]}"
                    insert_ticket(
                        None,
                        {
                            "ticket_id": ticket_id,
                            "status": "open",
                            "channel": "admin_escalation",
                            "opened_at": timestamp,
                        },
                    )
                    insert_approval(
                        None,
                        {
                            "approval_id": approval_id,
                            "status": "pending",
                            "resolved_at": "",
                        },
                    )
                    insert_edge_prompt_ticket(
                        None, prompt_id, ticket_id,
                        reason_code="HIGH_RISK", opened_at=timestamp,
                    )
                    insert_edge_ticket_approval(
                        None, ticket_id, approval_id,
                        status="pending", updated_at=timestamp,
                    )
            except Exception:
                pass

        # =========================
        # Audit / TigerGraph propagation (for UI)
        # =========================
        propagated = 0.0
        tg_affected: List[str] = []
        qp_ok = False
        if tg_ready:
            qp = query_risk_propagation(prompt_id)
            qp_ok = bool(qp.get("query_ok"))
            try:
                propagated = float(qp.get("propagated_risk") or 0.0)
            except Exception:
                propagated = 0.0
            propagated = max(0.0, min(1.0, propagated))
            tg_affected = list(qp.get("affected_systems") or [])
            if graph_logged and not tg_affected:
                tg_affected = ["api_core"]

        if not tg_ready:
            enforcement = "AI score only"
            tg_reason = "TigerGraph not configured — using AI score only."
        elif not graph_logged:
            enforcement = "AI score (TG fallback)"
            tg_reason = "TigerGraph logging failed or incomplete — using AI score."
        elif not qp_ok:
            enforcement = "AI score (TG fallback)"
            tg_reason = (
                "TigerGraph query did not return propagation data (install `risk_propagation` "
                "query or check REST++) — using AI score."
            )
        elif propagated == 0.0:
            enforcement = "AI score (TG fallback)"
            tg_reason = (
                "TigerGraph returned 0 propagated risk (graph chain may not be installed yet) "
                "– using AI score"
            )
        else:
            enforcement = "TigerGraph + AI"
            tg_reason = (
                f"TigerGraph propagated risk {propagated:.1%}; blended with policy / AI scoring."
            )

        audit = {
            "enforcement_engine": enforcement,
            "tg_propagated_risk": propagated,
            "tg_affected_systems": tg_affected,
            "tg_decision_reason": tg_reason,
        }

        # Also embed on `analysis` so any client that only reads `analysis` still gets audit UI fields.
        analysis["enforcement_engine"] = enforcement
        analysis["tg_propagated_risk"] = propagated
        analysis["tg_affected_systems"] = tg_affected
        analysis["tg_decision_reason"] = tg_reason

        # =========================

        # Top-level audit mirrors — some clients only read flat keys (avoids nested merge bugs).
        return {
            "status": "success",
            "analysis": analysis,
            "data": result,  # raw pipeline output (useful for debugging)
            "graph_logged": graph_logged,
            "prompt_id": prompt_id,
            "audit": audit,
            "enforcement_engine": enforcement,
            "tg_propagated_risk": propagated,
            "tg_affected_systems": tg_affected,
            "tg_decision_reason": tg_reason,
        }

    except Exception as e:
        print("ERROR OCCURRED:")
        print(traceback.format_exc())

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )