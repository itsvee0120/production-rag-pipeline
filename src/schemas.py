from typing import List, Literal

from pydantic import BaseModel


class RetrievedChunk(BaseModel):
    chunk_id: str  # internal chunk ID, or URL for web results
    content: str
    score: float  # similarity (stage 1) or sigmoid confidence (stage 2), in [0, 1]
    source: Literal["internal_doc", "web"]


class RAGResponse(BaseModel):
    answer: str
    citations: List[str]
    route_taken: Literal["INTERNAL_RAG", "WEB_FALLBACK"]
    confidence_score: float
    transformed_query: str
