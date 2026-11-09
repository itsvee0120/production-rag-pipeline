"""Threshold calibration: top cross-encoder (sigmoid) score on a small labeled query set.

Run: uv run python -m src.calibrate
Uses retriever + re-ranker only (no LLM calls, no rewriting), so results are free and deterministic.
"""

from src.reranker import THRESHOLD, Reranker
from src.retriever import Retriever

# label True = answerable from internal docs (should route INTERNAL_RAG)
LABELED = [
    ("How do I provision an isolated VPC in our staging environment?", True),
    ("What are the system requirements for Kubernetes worker nodes?", True),
    ("How do I roll back a production deployment?", True),
    ("When are production deploys allowed?", True),
    ("What does ERR_CHANGE_ID_REQUIRED mean?", True),
    ("Which EC2 instance families are approved?", True),
    ("How are shared platform costs charged back to teams?", True),
    ("What happens when a staging budget reaches 120%?", True),
    ("What changed in the v3 terraform network modules?", True),
    ("Can I create an isolated VPC with the terraform vpc module v2.9.1?", True),
    ("How do I fix ImagePullBackOff in an isolated VPC?", True),
    ("What is the CIDR block of the staging VPC?", True),
    ("How long are invoices kept?", True),
    ("Where is Terraform remote state stored?", True),
    ("What does the --canary flag do in infractl?", True),
    ("What was the root cause of the major AWS us-east-1 outage announced yesterday?", False),
    ("What's new in the Kubernetes release that came out this month?", False),
    ("How do I configure a VPC in Google Cloud Platform?", False),
    ("What is the pricing for Terraform Cloud?", False),
    ("What were the latest AWS re:Invent announcements?", False),
    ("How do I bake sourdough bread?", False),
    ("Who won the last FIFA World Cup?", False),
    ("What is the current price of Bitcoin?", False),
    ("What is the capital of Australia?", False),
    ("How do I center a div in CSS?", False),
]

THRESHOLDS = [0.3, 0.4, 0.5, 0.55, 0.6, 0.7, 0.8, 0.9]


def main() -> None:
    retriever, reranker = Retriever(), Reranker()
    scored = []
    for q, in_domain in LABELED:
        top = reranker.rerank(q, retriever.retrieve(q))[0]
        scored.append((q, in_domain, top.score, top.chunk_id))

    print("\nPer-query top score")
    print(f"{'label':<6} {'score':>6}  {'top chunk':<28} query")
    for q, in_domain, s, cid in sorted(scored, key=lambda x: -x[2]):
        print(f"{'IN' if in_domain else 'OUT':<6} {s:>6.3f}  {cid:<28} {q}")

    n_in = sum(1 for _, d, _, _ in scored if d)
    n_out = len(scored) - n_in
    print(f"\nThreshold sweep (IN={n_in}, OUT={n_out})")
    print("false fallback = in-domain sent to web | false internal = out-of-domain answered from docs (hallucination risk)")
    print(f"{'thr':>5} {'false fallback':>15} {'false internal':>15}")
    for t in THRESHOLDS:
        ff = sum(1 for _, d, s, _ in scored if d and s < t)
        fi = sum(1 for _, d, s, _ in scored if not d and s >= t)
        mark = "  <- current" if t == THRESHOLD else ""
        print(f"{t:>5.2f} {ff:>4}/{n_in} ({ff / n_in:4.0%}) {fi:>6}/{n_out} ({fi / n_out:4.0%}){mark}")


if __name__ == "__main__":
    main()
