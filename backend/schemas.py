from pydantic import BaseModel
from typing import Optional


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    history: Optional[list[ChatMessage]] = None


class ToolCall(BaseModel):
    name: str
    input: dict


class ToolResult(BaseModel):
    tool_name: str
    result: str


class ChatResponse(BaseModel):
    message: str
    tools_used: Optional[list[ToolCall]] = None
    thinking: Optional[str] = None
