import os

import pytest

from src.rewriter import rewrite


# Test 1: Conversational Pronoun Resolution (real LLM call)
@pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY not set")
def test_pronoun_resolution():
    history = ["Tell me about Kubernetes Worker Nodes in our EKS clusters."]
    out = rewrite("What are its system requirements?", history=history)
    assert "kubernetes worker nodes" in out.lower()
