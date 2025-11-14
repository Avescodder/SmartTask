from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500)


class Source(BaseModel):
    filename: str
    content: str
    similarity: float


class AnswerResponse(BaseModel):
    answer: str
    sources: List[Source]
    tokens_used: int
    response_time: float
    cached: bool = False


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    database: str
    redis: str
    documents_count: int


class DocumentUploadResponse(BaseModel):
    filename: str
    chunks_created: int
    status: str