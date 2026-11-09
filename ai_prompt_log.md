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
