from src.reranker import gate, sigmoid
from src.schemas import RetrievedChunk


def _chunk(cid: str, score: float) -> RetrievedChunk:
    return RetrievedChunk(chunk_id=cid, content="x", score=score, source="internal_doc")


# Test 2: Sigmoid Logit Normalization
def test_sigmoid_bounds():
    for logit in [-10.0, -3.5, -0.1, 0.1, 3.5, 10.0]:
        assert 0.0 < sigmoid(logit) < 1.0
    assert sigmoid(0.0) == 0.5
    assert sigmoid(-10.0) < 0.55 < sigmoid(10.0)
    # extreme logits must not overflow
    assert 0.0 <= sigmoid(-1000.0) <= 1.0 and 0.0 <= sigmoid(1000.0) <= 1.0


# Test 3: Threshold Gating Logic
def test_threshold_gating():
    status, top = gate([_chunk("a", 0.42), _chunk("b", 0.30)])
    assert status == "LOW_CONFIDENCE" and top == 0.42

    status, top = gate([_chunk("a", 0.81), _chunk("b", 0.10)])
    assert status == "HIGH_CONFIDENCE" and top == 0.81

    assert gate([])[0] == "LOW_CONFIDENCE"
