from pydantic import BaseModel
from typing import Optional

class EventPayload(BaseModel):
    event_type: str
    prompt_id: str
    prompt_text: Optional[str] = None
    risk_score: Optional[float] = 0.0
    intent: Optional[str] = None
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None
    agent_type: Optional[str] = None
    tool_id: Optional[str] = None
    tool_name: Optional[str] = None
    tool_risk: Optional[float] = 0.0
    action_id: Optional[str] = None
    action_name: Optional[str] = None
    action_severity: Optional[float] = 0.0
    system_id: Optional[str] = None
    system_name: Optional[str] = None
    system_criticality: Optional[float] = 0.0
    timestamp: Optional[str] = None

class ExecutionRequest(BaseModel):
    prompt_id: str
    action_name: str
