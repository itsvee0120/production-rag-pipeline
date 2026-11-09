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

## Phase 6: Web fallback
- **Prompt:** "next"
- **Generated:** `src/web_fallback.py` (Tavily if `TAVILY_API_KEY` is set to a real value, else DuckDuckGo; top 3 results as `RetrievedChunk(source="web", chunk_id=URL)`; snippets sanitized: HTML unescaped and stripped, `<external_web_source>` look-alikes removed so a snippet can't break out of the delimiters, control chars removed, truncated to 800 chars; non-http URLs dropped; returns `[]` on search failure).
- **Bugs/issues:** Smoke test with DuckDuckGo for "AWS us-east-1 outage root cause" returned irrelevant results (AWS homepage, console, American Welding Society) and a `duckduckgo_search` -> `ddgs` rename warning.
- **Fixes:** User set a real `TAVILY_API_KEY`; no code change. Rerun returned 3 relevant outage write-ups with URLs.

## Phase 7: Generator
- **Prompt:** "next"
- **Generated:** `src/generator.py` (Anthropic `claude-sonnet-5-5`, override via `ANTHROPIC_GENERATE_MODEL`; numbered sources, internal chunks in `<internal_doc>`, web chunks re-sanitized and wrapped in `<external_web_source>`; system prompt enforces grounding, inline `[n]` citations, and treats web content as data only; `citations[n-1]` maps `[n]` to chunk ID/URL; no LLM call when there are no chunks). `tests/test_pipeline_qa.py` with Test 6 (malicious snippet incl. a fake closing delimiter; asserts no "HACKED", answer still cites the legit source).
- **Bugs/issues:** none found.
- **Fixes:** none.

## Phase 8: Pipeline wiring + QA
- **Prompt:** "next"
- **Generated:** `src/pipeline.py` (rewrite -> retrieve K1=20 -> re-rank -> gate on top sigmoid score -> top K2=3 internal chunks or web search -> generate; returns `PipelineResult` with stage 1, re-ranked list, rank shifts, status and context for the UI). Tests 4 (in-domain VPC query routes `INTERNAL_RAG`, internal chunk IDs cited) and 5 (AWS outage query routes `WEB_FALLBACK`, citations are valid http(s) URLs) in `tests/test_pipeline_qa.py`.
- **Bugs/issues:** none found.
- **Fixes:** none.
