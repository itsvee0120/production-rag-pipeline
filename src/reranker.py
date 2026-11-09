import math
from typing import Dict, List, Literal, Tuple

import torch
from sentence_transformers import CrossEncoder

from src.schemas import RetrievedChunk

RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
THRESHOLD = 0.55
K2 = 3

Status = Literal["HIGH_CONFIDENCE", "LOW_CONFIDENCE"]


def sigmoid(x: float) -> float:
    """Map a raw cross-encoder logit to [0, 1] (numerically stable)."""
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    z = math.exp(x)
    return z / (1.0 + z)


def gate(reranked: List[RetrievedChunk], threshold: float = THRESHOLD) -> Tuple[Status, float]:
    """Gate on the top re-ranked (sigmoid) score."""
    top = reranked[0].score if reranked else 0.0
    return ("HIGH_CONFIDENCE" if top >= threshold else "LOW_CONFIDENCE"), top


def rank_shifts(before: List[RetrievedChunk], after: List[RetrievedChunk]) -> Dict[str, int]:
    """Positive = moved up after re-ranking."""
    old = {c.chunk_id: i for i, c in enumerate(before)}
    return {c.chunk_id: old[c.chunk_id] - i for i, c in enumerate(after) if c.chunk_id in old}


class Reranker:
    def __init__(self, model_name: str = RERANK_MODEL):
        # Identity activation so predict() returns raw logits; sigmoid is applied explicitly below.
        self.model = CrossEncoder(model_name, activation_fn=torch.nn.Identity())

    def rerank(self, query: str, candidates: List[RetrievedChunk]) -> List[RetrievedChunk]:
        if not candidates:
            return []
        logits = self.model.predict([(query, c.content) for c in candidates])
        scored = [c.model_copy(update={"score": sigmoid(float(l))}) for c, l in zip(candidates, logits)]
        return sorted(scored, key=lambda c: c.score, reverse=True)
