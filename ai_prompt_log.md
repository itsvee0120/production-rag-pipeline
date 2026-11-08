# AI Prompt Log

## Phase 0: Secrets setup
- **Prompt:** "Read CLAUDE.md and PLAN.md. Follow them strictly. Start with the remaining Phase 0 item (.env.example with placeholders only), then stop and wait for my go-ahead before Phase 1."
- **Generated:** `.env.example` content with placeholder `OPENAI_API_KEY` and `TAVILY_API_KEY` (from the assignment spec).
- **Bugs/issues:** The assistant's write to `.env.example` was blocked by the `.env*` deny rule in `.claude/settings.json`. Also noticed: `.gitignore` ignores `.claude/`, so `.claude/settings.json` is not committed.
- **Fixes:** `.env.example` content handed to the user to create manually. Deny rules left unchanged.
