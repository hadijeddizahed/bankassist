from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000, description="User's query")
    session_id: str | None = Field(default=None, description="Optional session ID")


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]
    session_id: str | None = None