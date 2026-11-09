# AI Prompt Log

## Phase 0: Secrets setup
- **Prompt:** "Read CLAUDE.md and PLAN.md. Follow them strictly. Start with the remaining Phase 0 item (.env.example with placeholders only), then stop and wait for my go-ahead before Phase 1."
- **Generated:** `.env.example` content with placeholder `OPENAI_API_KEY` and `TAVILY_API_KEY` (from the assignment spec).
- **Bugs/issues:** The assistant's write to `.env.example` was blocked by the `.env*` deny rule in `.claude/settings.json`. Also noticed: `.gitignore` ignores `.claude/`, so `.claude/settings.json` is not committed.
- **Fixes:** `.env.example` content handed to the user to create manually. Deny rules left unchanged. `.env.example` was missing from the Phase 0 commit; added in Phase 1.

## Phase 1: Project setup
- **Prompt:** "next steps", then approvals to fix `pyproject.toml`, remove the packaged layout, and remove the author email.
- **Generated:** `uv init` / `uv python pin 3.11` / `uv add` commands (run by user); `src/`, `tests/`, `docs/` layout with `__init__.py` files; `README.md` stub.
- **Bugs/issues:** `uv init` set `requires-python = ">=3.13"`, so `uv python pin 3.11` failed. `uv init` also created a packaged layout (`src/production_rag_pipeline/`, `[project.scripts]`, `[build-system]`) not matching the plan's flat `src/` files. Author email in `pyproject.toml`.
- **Fixes:** Changed `requires-python` to `">=3.11"`; removed the package dir, scripts and build-system blocks; removed the email.

## Phase 2: Knowledge base
- **Prompt:** "phase 2"
- **Generated:** 6 fictional internal docs in `docs/`: architecture, deployment runbook, VPC/networking (incl. isolated staging VPC), billing policy, Kubernetes worker nodes (system requirements), Terraform modules (current vs legacy versions). Written to cover the assignment's test queries (staging VPC, worker node requirements, older terraform modules) and include exact flags/IDs (`--isolated`, `CHG-XXXXX`, `INV-2026-004213`) for keyword-preservation checks.
- **Bugs/issues:** none found.
- **Fixes:** none.

## Phase 3: Schemas + retriever
- **Prompt:** "next, let's move through thing quickly"
- **Generated:** `src/schemas.py` (`RetrievedChunk`, `RAGResponse`); `src/retriever.py` (markdown split per `##` section, ChromaDB persistent collection with cosine space, `all-MiniLM-L6-v2`, K1=20, distance converted to similarity; indexing upserts only new/changed chunks by SHA-256 hash and deletes stale ones, so restarts don't re-embed or duplicate).
- **Bugs/issues:** none found.
- **Fixes:** none.

## Phase 4: Re-ranker + gate
- **Prompt:** "next"
- **Generated:** `src/reranker.py` (CrossEncoder `ms-marco-MiniLM-L-6-v2`, stable sigmoid on raw logits, `gate()` at 0.55 on top score, K2=3, `rank_shifts()`); `tests/test_reranker.py` (Test 2 sigmoid bounds, Test 3 gating 0.42 vs 0.81).
- **Bugs/issues:** none observed. Risk noted while writing: sentence-transformers' `CrossEncoder` can apply a default activation from the model config, so `predict()` is not guaranteed to return raw logits; sigmoid on top would double-squash.
- **Fixes:** Constructed `CrossEncoder` with `activation_fn=torch.nn.Identity()` so sigmoid is applied exactly once.

## Phase 5: Rewriter
- **Prompt:** "next"
- **Generated:** `src/rewriter.py` (LLM rewrite with history, 10 s timeout, no retries; empty query raises `EmptyQueryError`; any LLM failure returns the original query; flags and digit-bearing tokens like `CHG-12345` / `v3.4.0` are re-appended if the LLM dropped them); `tests/test_rewriter.py` (Test 1, skipped without an API key).
- **Bugs/issues:** First run: Test 1 skipped (no API key set). User then asked to switch from OpenAI to Anthropic.
- **Fixes:** Rewriter switched to the Anthropic Messages API (`claude-haiku-5-5`, override via `ANTHROPIC_REWRITE_MODEL`); test now checks `ANTHROPIC_API_KEY`.
- **Bug 2:** Test 1 failed: rewriter returned the original query. The fail-open `except` hid the cause; reproducing the exact call showed `TypeError: Messages.create() got an unexpected keyword argument 'temperature'` (installed `anthropic` SDK).
- **Fix 2:** Removed `temperature=0` from the rewriter call.
