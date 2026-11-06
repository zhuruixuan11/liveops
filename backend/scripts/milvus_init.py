"""Milvus 知识库向量化入库（一次性 job，幂等）。

运行：python -m scripts.milvus_init
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.llm_client import get_llm
from app.core.config import get_settings
from app.models.all import KbDoc

settings = get_settings()


def _try_milvus():
    try:
        from pymilvus import MilvusClient
        return MilvusClient(uri=f"http://{settings.milvus_host}:{settings.milvus_port}")
    except Exception as e:
        print(f"[milvus] pymilvus 不可用: {e}")
        return None


def main():
    llm = get_llm()
    client = _try_milvus()
    dim = settings.embedding_dim

    with SessionLocal() as db:
        docs = db.execute(select(KbDoc).where(KbDoc.milvus_id.is_(None))).scalars().all()
        print(f"待入库知识库条目: {len(docs)}")

    if client:
        client.create_collection(
            collection_name="kb_docs", dimension=dim,
            auto_id=True, vector_field_name="embedding",
        )

    batch_size = 16
    for i in range(0, len(docs), batch_size):
        batch = docs[i:i + batch_size]
        texts = [d.chunk_text for d in batch]
        embs = llm.embed(texts)
        if not embs:
            print("embedding 失败（无 API key 或网络问题），跳过 milvus 入库")
            break
        if client:
            client.insert(
                collection_name="kb_docs",
                data=[
                    {"doc_id": d.doc_id, "category": d.category, "embedding": emb}
                    for d, emb in zip(batch, embs)
                ],
            )
        with SessionLocal() as db:
            for d in batch:
                d2 = db.get(KbDoc, d.doc_id)
                d2.milvus_id = f"local-{d.doc_id}"
            db.commit()
        print(f"[{i+batch_size}/{len(docs)}] 已入库")

    print("完成")


if __name__ == "__main__":
    main()
