from dataclasses import dataclass
from typing import Dict, List, Optional

from src.generator import generate
from src.reranker import K2, Reranker, Status, gate, rank_shifts
from src.retriever import Retriever
from src.rewriter import rewrite
from src.schemas import RAGResponse, RetrievedChunk
from src.web_fallback import web_search


@dataclass
class PipelineResult:
    response: RAGResponse
    stage1: List[RetrievedChunk]  # bi-encoder top K1, score = cosine similarity
    reranked: List[RetrievedChunk]  # all candidates, score = sigmoid confidence, sorted
    shifts: Dict[str, int]  # chunk_id -> rank change (positive = moved up)
    status: Status
    context: List[RetrievedChunk]  # chunks sent to the generator


class Pipeline:
    def __init__(self, retriever: Optional[Retriever] = None, reranker: Optional[Reranker] = None):
        self.retriever = retriever or Retriever()
        self.reranker = reranker or Reranker()

    def run(self, query: str, history: Optional[List[str]] = None) -> PipelineResult:
        transformed = rewrite(query, history)  # raises EmptyQueryError on empty input
        stage1 = self.retriever.retrieve(transformed)
        reranked = self.reranker.rerank(transformed, stage1)
        status, top = gate(reranked)

        if status == "HIGH_CONFIDENCE":
            route, context = "INTERNAL_RAG", reranked[:K2]
        else:
            route, context = "WEB_FALLBACK", web_search(transformed)

        response = generate(transformed, context, route=route, confidence=top)
        return PipelineResult(
            response=response,
            stage1=stage1,
            reranked=reranked,
            shifts=rank_shifts(stage1, reranked),
            status=status,
            context=context,
        )
