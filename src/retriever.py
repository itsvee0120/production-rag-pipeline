import hashlib
from pathlib import Path
from typing import List

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from src.schemas import RetrievedChunk

ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT / "docs"
DB_DIR = ROOT / "chroma_db"
COLLECTION = "internal_docs"
EMBED_MODEL = "all-MiniLM-L6-v2"
K1 = 20


def chunk_markdown(path: Path) -> List[tuple[str, str]]:
    """Split a markdown file into one chunk per '## ' section, prefixed with the doc title."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    title = lines[0].lstrip("# ").strip() if lines else path.stem
    sections, current = [], []
    for line in lines[1:]:
        if line.startswith("## ") and current:
            sections.append("\n".join(current).strip())
            current = []
        current.append(line)
    if current:
        sections.append("\n".join(current).strip())
    return [
        (f"{path.stem}#{i}", f"{title}\n{body}")
        for i, body in enumerate(s for s in sections if s)
    ]


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class Retriever:
    def __init__(self, docs_dir: Path = DOCS_DIR, db_dir: Path = DB_DIR):
        self.client = chromadb.PersistentClient(path=str(db_dir))
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION,
            embedding_function=SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL),
            configuration={"hnsw": {"space": "cosine"}},
        )
        self.index(docs_dir)

    def index(self, docs_dir: Path) -> int:
        """Embed only new or changed chunks; remove chunks that no longer exist. Returns count embedded."""
        chunks = {cid: text for p in sorted(docs_dir.glob("*.md")) for cid, text in chunk_markdown(p)}
        existing = self.collection.get(include=["metadatas"])
        stored = {cid: (m or {}).get("hash") for cid, m in zip(existing["ids"], existing["metadatas"])}

        to_upsert = [cid for cid, text in chunks.items() if stored.get(cid) != _hash(text)]
        stale = [cid for cid in stored if cid not in chunks]

        if to_upsert:
            self.collection.upsert(
                ids=to_upsert,
                documents=[chunks[c] for c in to_upsert],
                metadatas=[{"hash": _hash(chunks[c])} for c in to_upsert],
            )
        if stale:
            self.collection.delete(ids=stale)
        return len(to_upsert)

    def retrieve(self, query: str, k: int = K1) -> List[RetrievedChunk]:
        res = self.collection.query(query_texts=[query], n_results=min(k, self.collection.count()))
        return [
            RetrievedChunk(
                chunk_id=cid,
                content=doc,
                score=max(0.0, 1.0 - dist),  # cosine distance -> similarity
                source="internal_doc",
            )
            for cid, doc, dist in zip(res["ids"][0], res["documents"][0], res["distances"][0])
        ]
