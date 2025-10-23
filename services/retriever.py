import os
from typing import List, Dict, Any

import chromadb
from sentence_transformers import SentenceTransformer


EMBED_MODEL = os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2")
CHROMA_DIR = os.getenv("CHROMA_DIR", "./chroma_db")
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "global_kb")

_embedder = None
_client = None
_collection = None


def _get_embedder() -> SentenceTransformer:
    global _embedder
    if _embedder is None:
        os.environ.setdefault("USE_TF", "0")
        _embedder = SentenceTransformer(EMBED_MODEL)
    return _embedder


def _get_collection():
    global _client, _collection
    if _client is None:
        os.environ.setdefault("ANONYMIZED_TELEMETRY", "false")
        _client = chromadb.PersistentClient(path=CHROMA_DIR)
    if _collection is None:
        _collection = _client.get_or_create_collection(
            CHROMA_COLLECTION, metadata={"hnsw:space": "cosine"}
        )
    return _collection


def retrieve_docs(event_input: Dict[str, Any], top_k: int = 12) -> List[Dict[str, Any]]:
    # Use event_name + event_type as retrieval query
    query = f"{event_input.get('event_name','')} {event_input.get('event_type','')}".strip()
    if not query:
        return []

    collection = _get_collection()
    embedder = _get_embedder()
    q_emb = embedder.encode([query]).tolist()[0]
    res = collection.query(query_embeddings=[q_emb], n_results=top_k)

    if not res or not res.get("ids") or not res["ids"]:
        return []

    out: List[Dict[str, Any]] = []
    for i in range(len(res["ids"][0])):
        meta = res["metadatas"][0][i] if res.get("metadatas") else {}
        doc_id = res["ids"][0][i]
        text = res["documents"][0][i] if res.get("documents") else ""
        if isinstance(meta, dict):
            meta.setdefault("doc_id", doc_id)
        out.append({"doc_id": doc_id, "text": text, "metadata": meta})
    return out
