from pydantic import BaseModel


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    agent: str
    confidence: float
    client_profile: dict


class ResetRequest(BaseModel):
    session_id: str
