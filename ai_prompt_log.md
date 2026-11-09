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

## Phase 9: AI audit (four RAG failure modes)
- **Prompt:** "next"
- **Note:** The code was generated with the CLAUDE.md rules in context, so the safeguards were built in from the start rather than added to a naive draft. This audit checks the generated code as it stands.

| Failure mode | Where | Finding | Refactor |
|---|---|---|---|
| Logit scaling | `src/reranker.py` | Sigmoid applied to logits; `gate()` compares top sigmoid score to 0.55. Risk: `CrossEncoder` may apply a config default activation, causing a double sigmoid. | `CrossEncoder(..., activation_fn=torch.nn.Identity())` (Phase 4). Tests 2, 3 cover bounds and gating. |
| Web prompt injection | `src/web_fallback.py`, `src/generator.py` | Snippets sanitized (HTML, control chars, fake delimiters) and wrapped in `<external_web_source>`; system prompt says data only. **Gap found:** the URL was put into `url="..."` without escaping quotes, so a crafted URL could break out of the attribute. | `html.escape(..., quote=True)` on the URL attribute. Test 6 covers the injected-instruction case. |
| Rewriter failure | `src/rewriter.py` | Empty query raises `EmptyQueryError`; 10 s timeout, no retries, falls back to the original query; flags/IDs re-appended if dropped. **Gap found (observed in Phase 5):** the bare `except` silently hid a real bug (`temperature` TypeError), making Test 1 fail with no clue why. | Log a warning with the exception before falling back. |
| Vector duplication | `src/retriever.py` | Chunks upserted only when their SHA-256 hash changed; stale IDs deleted. Verified in Phase 3: `count 41 reembedded 0`. | None needed. |

## Phase 10: UI
- **Prompt:** "next"
- **Generated:** `src/app.py` (Streamlit): query form, multi-turn toggle with session history and clear button; sidebar with transformed query, route badge (🟢 INTERNAL_RAG / 🟠 WEB_FALLBACK), confidence metric + progress bar vs 0.55; answer with one popover per `[n]` source (web URL link or chunk ID, content shown as plain text so untrusted web text is never rendered as markdown); collapsible Stage 1 top-20 table (cosine similarity) and Stage 2 top-5 table with stage-1 rank and ↑/↓ shift. Pipeline cached with `st.cache_resource`.
- **Bugs/issues (caught while writing, not observed at runtime):** `streamlit run src/app.py` puts `src/` (not the project root) on `sys.path`, so `from src...` imports would fail. Also `use_container_width` is deprecated in the installed Streamlit.
- **Fixes:** Insert project root into `sys.path` at the top of `app.py`; removed `use_container_width` (default width is already `stretch`).

## Phase 11: Threshold calibration
- **Prompt:** "next phase"
- **Generated:** `src/calibrate.py`: 25 labeled queries (15 in-domain, 10 out-of-domain incl. near-domain hard negatives), top sigmoid score per query via retriever + re-ranker (no LLM, no rewrite), sweep of thresholds 0.3-0.9 counting false fallbacks (in-domain sent to web) and false internals (out-of-domain answered from docs).
- **Results:** In-domain scores 0.952-1.000 except one; out-of-domain 0.000-0.033 except one. At 0.55: 1/15 false fallback, 1/10 false internal. At 0.80-0.90: 1/15 false fallback, 0/10 false internal.
  - False internal: "How do I configure a VPC in Google Cloud Platform?" scored 0.739 (matched `03_vpc_networking#2`).
  - False fallback at every threshold: "What does the --canary flag do in infractl?" scored 0.014 (re-ranker under-scores the flags chunk).
- **Decision:** Keep 0.55 (assignment spec). Rationale: scores are strongly bimodal so 0.55 sits in a wide gap; 0.80 removed the one hard-negative false internal on this set, but 25 queries is too small to justify deviating from the spec. Both misses recorded as known limitations.
- **Bugs/issues:** Re-ranker miss on the `--canary` flag query (not fixable by threshold).
- **Fixes:** none (documented as a limitation).

## Phase 12: Deployment (Option B, Docker)
- **Prompt:** "do just B"
- **Generated:** `Dockerfile` (python:3.11-slim, uv, `uv sync --frozen --no-dev` from the lockfile, copies `src/` and `docs/`, Streamlit on 0.0.0.0:8501); `docker-compose.yml` (port 8501, `.env` loaded at runtime via `env_file`, named volumes for `chroma_db` and the Hugging Face model cache); `.dockerignore` (excludes `.env*`, local-only docs, `.git`, `.venv`, `chroma_db`, tests).
- **Bugs/issues:** First `docker compose up --build` was extremely slow (image unpack step ran 4000+ s): the locked Linux `torch` wheel pulls multi-GB CUDA libraries the app never uses.
- **Fixes:** Pinned `torch` to the PyTorch CPU index via `[tool.uv.sources]` / `[[tool.uv.index]]` in `pyproject.toml` and added `torch` as a direct dependency. Rebuild finished in ~6.5 min; container runs and the UI works. (Local environment issues along the way, not code: C: drive full, Docker disk moved to D:, port 8501 held by another project's container.)
