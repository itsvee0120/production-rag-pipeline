import logging
import os
import re
from typing import List, Optional

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
log = logging.getLogger(__name__)

MODEL = os.getenv("ANTHROPIC_REWRITE_MODEL", "claude-haiku-5-5")
TIMEOUT_S = 10.0

SYSTEM_PROMPT = """You rewrite user questions into standalone search queries for an internal cloud infrastructure knowledge base.
Rules:
- Resolve pronouns and vague references ("it", "that", "we used last month") using the conversation history. Use the exact entity names from the history.
- Remove conversational filler.
- Preserve exactly, character for character: CLI flags (e.g. --isolated), IDs and serial numbers (e.g. CHG-12345), version numbers, error codes, CIDRs, and quoted or backticked terms.
- If the question is already standalone, return it nearly unchanged.
- Output only the rewritten query, nothing else."""

# Flags (--dry-run, -n) and any token containing a digit (CHG-12345, v3.4.0, 10.21.16.0/20).
_PROTECTED = re.compile(r"(?<!\S)--?[A-Za-z][\w-]*|\S*\d\S*")


class EmptyQueryError(ValueError):
    pass


def protected_tokens(query: str) -> List[str]:
    return [t.strip("?.,!;:\"'()") for t in _PROTECTED.findall(query)]


def rewrite(query: str, history: Optional[List[str]] = None, client: Optional[Anthropic] = None) -> str:
    """Return a standalone search query. Falls back to the original query on any LLM failure."""
    if not query or not query.strip():
        raise EmptyQueryError("Query must not be empty.")
    query = query.strip()

    history_text = "\n".join(f"- {h}" for h in (history or [])) or "(none)"
    try:
        client = client or Anthropic(timeout=TIMEOUT_S, max_retries=0)
        resp = client.messages.create(
            model=MODEL,
            max_tokens=200,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": f"Conversation history:\n{history_text}\n\nQuestion: {query}"},
            ],
        )
        rewritten = "".join(b.text for b in resp.content if b.type == "text").strip()
    except Exception as e:
        log.warning("Rewriter failed, using original query: %r", e)
        return query  # fail open: timeout, network, auth, etc.

    if not rewritten:
        return query
    missing = [t for t in protected_tokens(query) if t and t not in rewritten]
    return f"{rewritten} {' '.join(missing)}" if missing else rewritten
