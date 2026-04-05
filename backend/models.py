from pydantic import BaseModel

class PromptRecord(BaseModel):
    id: int
    prompt: str
    risk_score: float
    intent: str
