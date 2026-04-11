import os
import requests
from dotenv import load_dotenv

load_dotenv(override=True)

TG_HOST = os.getenv("TG_HOST")
TG_TOKEN = os.getenv("TG_TOKEN")
TG_GRAPH = os.getenv("TG_GRAPH")


def _normalize_host(host: str) -> str:
    return (host or "").strip().rstrip("/")


HOST = _normalize_host(TG_HOST)
BASE_URL = f"{HOST}/restpp/graph/{TG_GRAPH}" if HOST and TG_GRAPH else ""

HEADERS = {
    "Authorization": f"Bearer {TG_TOKEN}",
    "Content-Type": "application/json",
}


def get_conn():
    """Legacy hook for callers that expect a connection object; REST uses no persistent conn."""
    return None


def get_vertices(vertex_type: str):
    if not BASE_URL:
        return []
    url = f"{BASE_URL}/vertices/{vertex_type}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=5)
        return r.json() if r.ok else []
    except Exception:
        return []


def _post(payload):
    url = BASE_URL

    print("\n========== TIGERGRAPH REQUEST ==========")
    print("URL:", url)
    print("PAYLOAD:", payload)
    print("========================================\n")

    try:
        if not url:
            return {"error": "TigerGraph not configured (missing TG_HOST/TG_GRAPH)"}

        response = requests.post(
            url,
            headers=HEADERS,
            json=payload,
            timeout=5,
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


# --- Vertices ---


def insert_user(_, data):
    return _post({
        "vertices": {
            "User": {
                data["user_id"]: {
                    "email": {"value": data.get("email") or ""},
                    "role": {"value": data.get("role") or "user"},
                }
            }
        }
    })


def insert_session(_, data):
    return _post({
        "vertices": {
            "Session": {
                data["session_id"]: {
                    "label": {"value": data.get("label") or "web"},
                    "session_risk": {"value": float(data.get("session_risk") or 0.0)},
                }
            }
        }
    })


def insert_prompt(_, data):
    return _post({
        "vertices": {
            "Prompt": {
                data["prompt_id"]: {
                    "text": {"value": data["text"]},
                    "risk_score": {"value": data["risk_score"]},
                    "intent": {"value": data["intent"]},
                    "timestamp": {"value": data["timestamp"]},
                    "status": {"value": data["status"]},
                }
            }
        }
    })


def insert_policy_rule(_, data):
    return _post({
        "vertices": {
            "PolicyRule": {
                data["rule_id"]: {
                    "rule_name": {"value": data.get("rule_name") or "default"},
                    "sensitivity": {"value": data.get("sensitivity") or "internal"},
                }
            }
        }
    })


def insert_dataclass(_, data):
    return _post({
        "vertices": {
            "DataClass": {
                data["class_id"]: {
                    "label": {"value": data.get("label") or "generic"},
                    "tier": {"value": float(data.get("tier") or 1.0)},
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
                    "agent_type": {"value": data["agent_type"]},
                }
            }
        }
    })


def insert_model_provider(_, data):
    return _post({
        "vertices": {
            "ModelProvider": {
                data["provider_id"]: {
                    "vendor": {"value": data.get("vendor") or "unknown"},
                    "model_name": {"value": data.get("model_name") or "default"},
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
                    "risk_level": {"value": float(data["risk_level"])},
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
                    "severity": {"value": float(data["severity"])},
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
                    "criticality": {"value": float(data["criticality"])},
                }
            }
        }
    })


def insert_control(_, data):
    return _post({
        "vertices": {
            "Control": {
                data["control_id"]: {
                    "name": {"value": data.get("name") or "control"},
                    "effectiveness": {"value": float(data.get("effectiveness") or 0.25)},
                }
            }
        }
    })


def insert_ticket(_, data):
    return _post({
        "vertices": {
            "Ticket": {
                data["ticket_id"]: {
                    "status": {"value": data.get("status") or "open"},
                    "channel": {"value": data.get("channel") or "escalation"},
                    "opened_at": {"value": data.get("opened_at") or ""},
                }
            }
        }
    })


def insert_approval(_, data):
    return _post({
        "vertices": {
            "Approval": {
                data["approval_id"]: {
                    "status": {"value": data.get("status") or "pending"},
                    "resolved_at": {"value": data.get("resolved_at") or ""},
                }
            }
        }
    })


# --- Edges (weights / time / revocation) ---


def insert_edge_user_session(_, user_id, session_id, confidence=1.0, observed_at="", revoked=0):
    return _post({
        "edges": {
            "User": {
                user_id: {
                    "USER_OWNS_SESSION": {
                        "Session": {
                            session_id: {
                                "confidence": {"value": float(confidence)},
                                "observed_at": {"value": observed_at},
                                "revoked": {"value": int(revoked)},
                            }
                        }
                    }
                }
            }
        }
    })


def insert_edge_session_prompt(_, session_id, prompt_id, confidence=1.0, observed_at="", revoked=0):
    return _post({
        "edges": {
            "Session": {
                session_id: {
                    "SESSION_SUBMITS_PROMPT": {
                        "Prompt": {
                            prompt_id: {
                                "confidence": {"value": float(confidence)},
                                "observed_at": {"value": observed_at},
                                "revoked": {"value": int(revoked)},
                            }
                        }
                    }
                }
            }
        }
    })


def insert_edge_policy_prompt(_, rule_id, prompt_id, severity_weight=1.0):
    return _post({
        "edges": {
            "PolicyRule": {
                rule_id: {
                    "POLICY_APPLIES_TO": {
                        "Prompt": {
                            prompt_id: {
                                "severity_weight": {"value": float(severity_weight)},
                            }
                        }
                    }
                }
            }
        }
    })


def insert_edge_dataclass_system(_, class_id, system_id, coverage=1.0):
    return _post({
        "edges": {
            "DataClass": {
                class_id: {
                    "DATACLASS_LABELS_SYSTEM": {
                        "System": {
                            system_id: {
                                "coverage": {"value": float(coverage)},
                            }
                        }
                    }
                }
            }
        }
    })


def insert_edge_prompt_agent(
    _,
    prompt_id,
    agent_id,
    risk_passed_or_success=True,
    *,
    confidence=0.95,
    observed_at="",
    revoked=0,
):
    # api/main: bool; backend/main: numeric risk_score (0–100 or 0–1)
    if isinstance(risk_passed_or_success, bool):
        risk_passed = 1.0 if risk_passed_or_success else 0.0
    else:
        try:
            x = float(risk_passed_or_success)
            risk_passed = x / 100.0 if x > 1.0 else x
        except (TypeError, ValueError):
            risk_passed = 1.0
    return _post({
        "edges": {
            "Prompt": {
                prompt_id: {
                    "PROMPT_TRIGGERS_AGENT": {
                        "Agent": {
                            agent_id: {
                                "risk_passed": {"value": float(risk_passed)},
                                "confidence": {"value": float(confidence)},
                                "observed_at": {"value": observed_at},
                                "revoked": {"value": int(revoked)},
                            }
                        }
                    }
                }
            }
        }
    })


def insert_edge_agent_model(
    _, agent_id, provider_id, confidence=0.98, observed_at="", revoked=0
):
    return _post({
        "edges": {
            "Agent": {
                agent_id: {
                    "AGENT_ROUTES_TO_MODEL": {
                        "ModelProvider": {
                            provider_id: {
                                "confidence": {"value": float(confidence)},
                                "observed_at": {"value": observed_at},
                                "revoked": {"value": int(revoked)},
                            }
                        }
                    }
                }
            }
        }
    })


def insert_edge_model_tool(
    _, provider_id, tool_id, weight=0.9, observed_at="", revoked=0
):
    return _post({
        "edges": {
            "ModelProvider": {
                provider_id: {
                    "MODEL_INVOKES_TOOL": {
                        "Tool": {
                            tool_id: {
                                "weight": {"value": float(weight)},
                                "observed_at": {"value": observed_at},
                                "revoked": {"value": int(revoked)},
                            }
                        }
                    }
                }
            }
        }
    })


def insert_edge_agent_tool(
    _,
    agent_id,
    tool_id,
    timestamp,
    *,
    confidence=0.85,
    observed_at="",
    revoked=0,
):
    return _post({
        "edges": {
            "Agent": {
                agent_id: {
                    "AGENT_USES_TOOL": {
                        "Tool": {
                            tool_id: {
                                "timestamp": {"value": timestamp},
                                "confidence": {"value": float(confidence)},
                                "observed_at": {"value": observed_at},
                                "revoked": {"value": int(revoked)},
                            }
                        }
                    }
                }
            }
        }
    })


def insert_edge_tool_action(
    _,
    tool_id,
    action_id,
    timestamp,
    *,
    weight=0.9,
    observed_at="",
    revoked=0,
):
    return _post({
        "edges": {
            "Tool": {
                tool_id: {
                    "TOOL_EXECUTES_ACTION": {
                        "Action": {
                            action_id: {
                                "timestamp": {"value": timestamp},
                                "weight": {"value": float(weight)},
                                "observed_at": {"value": observed_at},
                                "revoked": {"value": int(revoked)},
                            }
                        }
                    }
                }
            }
        }
    })


def insert_edge_action_system(
    _,
    action_id,
    system_id,
    impact_score,
    *,
    observed_at="",
    revoked=0,
):
    return _post({
        "edges": {
            "Action": {
                action_id: {
                    "ACTION_AFFECTS_SYSTEM": {
                        "System": {
                            system_id: {
                                "impact_score": {"value": float(impact_score)},
                                "observed_at": {"value": observed_at},
                                "revoked": {"value": int(revoked)},
                            }
                        }
                    }
                }
            }
        }
    })


# --- Legacy edge payloads (subset of attrs) — works on older AIRiskGraph schemas ---


def insert_edge_prompt_agent_legacy(_, prompt_id, agent_id, risk_passed=1.0):
    return _post({
        "edges": {
            "Prompt": {
                prompt_id: {
                    "PROMPT_TRIGGERS_AGENT": {
                        "Agent": {
                            agent_id: {
                                "risk_passed": {"value": float(risk_passed)},
                            }
                        }
                    }
                }
            }
        }
    })


def insert_edge_agent_tool_legacy(_, agent_id, tool_id, timestamp):
    return _post({
        "edges": {
            "Agent": {
                agent_id: {
                    "AGENT_USES_TOOL": {
                        "Tool": {
                            tool_id: {
                                "timestamp": {"value": timestamp},
                            }
                        }
                    }
                }
            }
        }
    })


def insert_edge_tool_action_legacy(_, tool_id, action_id, timestamp):
    return _post({
        "edges": {
            "Tool": {
                tool_id: {
                    "TOOL_EXECUTES_ACTION": {
                        "Action": {
                            action_id: {
                                "timestamp": {"value": timestamp},
                            }
                        }
                    }
                }
            }
        }
    })


def insert_edge_action_system_legacy(_, action_id, system_id, impact_score):
    return _post({
        "edges": {
            "Action": {
                action_id: {
                    "ACTION_AFFECTS_SYSTEM": {
                        "System": {
                            system_id: {
                                "impact_score": {"value": float(impact_score)},
                            }
                        }
                    }
                }
            }
        }
    })


def insert_edge_action_mitigated(
    _, action_id, control_id, mitigated_at="", confidence=0.9
):
    return _post({
        "edges": {
            "Action": {
                action_id: {
                    "ACTION_MITIGATED_BY": {
                        "Control": {
                            control_id: {
                                "mitigated_at": {"value": mitigated_at},
                                "confidence": {"value": float(confidence)},
                            }
                        }
                    }
                }
            }
        }
    })


def insert_edge_prompt_ticket(_, prompt_id, ticket_id, reason_code="", opened_at=""):
    return _post({
        "edges": {
            "Prompt": {
                prompt_id: {
                    "PROMPT_RAISES_TICKET": {
                        "Ticket": {
                            ticket_id: {
                                "reason_code": {"value": reason_code},
                                "opened_at": {"value": opened_at},
                            }
                        }
                    }
                }
            }
        }
    })


def insert_edge_ticket_approval(_, ticket_id, approval_id, status="pending", updated_at=""):
    return _post({
        "edges": {
            "Ticket": {
                ticket_id: {
                    "TICKET_AWAITING_APPROVAL": {
                        "Approval": {
                            approval_id: {
                                "status": {"value": status},
                                "updated_at": {"value": updated_at},
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


def query_risk_propagation(prompt_id: str) -> dict:
    """
    Run installed query `risk_propagation` via REST++.
    Returns propagated_risk (0–1), affected_systems (names), query_ok.
    """
    out = {
        "propagated_risk": 0.0,
        "affected_systems": [],
        "query_ok": False,
        "detail": None,
    }
    if not HOST or not TG_GRAPH or not TG_TOKEN:
        out["detail"] = "not_configured"
        return out

    url = f"{HOST}/restpp/query/{TG_GRAPH}/risk_propagation"
    def _unwrap_first_scalar(val):
        """REST++ PRINT often nests values as [[x]] or [[[x]]]."""
        v = val
        for _ in range(6):
            if isinstance(v, (list, tuple)) and len(v) == 1:
                v = v[0]
            else:
                break
        return v

    def _to_float_safe(val) -> float:
        try:
            v = _unwrap_first_scalar(val)
            return float(v)
        except (TypeError, ValueError):
            return 0.0

    try:
        resp = requests.get(
            url,
            headers=HEADERS,
            params={"prompt_id": prompt_id},
            timeout=8,
        )
        if not resp.ok:
            out["detail"] = f"http_{resp.status_code}"
            try:
                out["detail"] = (resp.json() or {}).get("message") or out["detail"]
            except Exception:
                pass
            return out
        data = resp.json()
    except Exception as e:
        out["detail"] = str(e)
        return out

    if isinstance(data, dict) and data.get("error"):
        out["detail"] = data.get("message") or "query_error"
        return out

    results = []
    if isinstance(data, dict):
        results = data.get("results") or data.get("Result") or []
    if not isinstance(results, list):
        results = []

    affected: list = []
    propagated = 0.0

    def _walk(obj, depth: int = 0):
        """Collect floats / strings from nested PRINT structures (TG 3.x / 4.x)."""
        nonlocal propagated, affected
        if depth > 12:
            return
        if isinstance(obj, dict):
            for key, val in obj.items():
                lk = str(key).lower()
                if "affected" in lk:
                    if isinstance(val, (list, tuple)):
                        for item in val:
                            if isinstance(item, (list, tuple)):
                                for x in item:
                                    if x is not None:
                                        affected.append(str(x))
                            elif item is not None:
                                affected.append(str(item))
                    elif val is not None:
                        affected.append(str(val))
                elif "total_propagated" in lk or lk.endswith("propagated_risk"):
                    propagated = max(propagated, _to_float_safe(val))
                else:
                    _walk(val, depth + 1)
        elif isinstance(obj, (list, tuple)):
            for item in obj:
                _walk(item, depth + 1)

    for block in results:
        _walk(block)

    out["affected_systems"] = list(dict.fromkeys(affected))
    raw = float(propagated)
    if raw <= 1.0:
        norm = max(0.0, min(1.0, raw))
    else:
        norm = max(0.0, min(1.0, raw / 100.0))
    out["propagated_risk"] = norm
    out["query_ok"] = True
    return out
