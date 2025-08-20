from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ChatRequest(BaseModel):
    conversation_id: str = Field(..., description="Unique ID for a conversation/session")
    message: str = Field(..., description="User message in Korean")
    top_k: Optional[int] = None

class ChatChunk(BaseModel):
    type: str
    content: str
    meta: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    answer: str
    sources: List[Dict[str, str]]  # title, url, id
    suggestions: List[str]

class IndexRequest(BaseModel):
    pkl_path: str = Field(..., description="Path to final_result.pkl")
    reset: bool = Field(default=False, description="Whether to wipe existing vector store")

class Message(BaseModel):
    role: str
    content: str

class ConversationHistory(BaseModel):
    conversation_id: str
    messages: List[Message]
