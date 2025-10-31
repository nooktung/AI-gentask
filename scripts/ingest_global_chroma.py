import os, json
from sentence_transformers import SentenceTransformer
import chromadb

# ====== Cấu hình ======
DATA_DIR = "./kb/global"        # Thư mục chứa các file JSON tài liệu (đã sửa để khớp repo)
CHROMA_DIR = "./chroma_db"           # Thư mục lưu vector database
COLLECTION_NAME = "global_kb"        # Tên collection trong Chroma
EMBED_MODEL = os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2")


# ====== Chuẩn bị ChromaDB và Embedder ======
def get_chroma_collection():
    os.environ.setdefault("ANONYMIZED_TELEMETRY", "false")
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    col = client.get_or_create_collection(COLLECTION_NAME, metadata={"hnsw:space": "cosine"})
    return col


def get_embedder():
    os.environ.setdefault("USE_TF", "0")
    return SentenceTransformer(EMBED_MODEL)


# ====== Hàm xử lý ======
def build_metadata(doc: dict):
    """Chuyển dữ liệu context thành metadata phẳng, tương thích Chroma 1.1.x"""
    ctx_tags = doc.get("context_tags", [])
    etypes = doc.get("event_type", [])

    return {
        "event_type_primary": etypes[0] if etypes else "",
        "tag_vip": "vip" in ctx_tags,
        "tag_sponsor": "sponsor" in ctx_tags,
        "tag_outdoor": "outdoor" in ctx_tags,
    }


def ingest():
    print("Starting KB ingestion...")
    embedder = get_embedder()
    col = get_chroma_collection()

    all_docs, all_ids, all_metas, all_embs = [], [], [], []

    # ====== Read JSON files ======
    for file in os.listdir(DATA_DIR):
        if not file.endswith(".json"):
            continue
        path = os.path.join(DATA_DIR, file)
        with open(path, "r", encoding="utf-8") as f:
            doc = json.load(f)

        doc_id = doc.get("doc_id") or os.path.splitext(file)[0]
        meta = build_metadata(doc)

        # Convert baseline_tasks to text
        tasks = doc.get("baseline_tasks", [])
        text_parts = []
        for t in tasks:
            description = t.get('description') or t.get('notes') or 'No description'
            part = f"{t['name']} ({t['owner_department']}): {description}"
            text_parts.append(part)
        text_join = "\n".join(text_parts)

        all_ids.append(doc_id)
        all_docs.append(text_join)
        all_metas.append(meta)

    # ====== Create embeddings ======
    print(f"Creating embeddings for {len(all_docs)} documents...")
    all_embs = embedder.encode(all_docs, show_progress_bar=True).tolist()

    # ====== Upsert to Chroma ======
    print(f"Upserting to collection '{COLLECTION_NAME}'...")
    col.upsert(ids=all_ids, documents=all_docs, metadatas=all_metas, embeddings=all_embs)

    print("Ingestion completed!")
    print(f"Total: {len(all_ids)} documents added.")


if __name__ == "__main__":
    ingest()
