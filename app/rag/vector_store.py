# vector_store.py file

from typing import Dict, List
import psycopg2
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer
from app.config import settings
from app.logging_config import logger
from app.rag.knowledge_base import KNOWLEDGE_BASE


class VectorStore:
    def __init__(self) -> None:
        self._embedder = SentenceTransformer(settings.EMBEDDING_MODEL)
        self._conn = psycopg2.connect(settings.DATABASE_URL)
        self._conn.autocommit = True
        register_vector(self._conn)
        self._ensure_schema()
        self._build()

    def _ensure_schema(self) -> None:
        with self._conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS knowledge_base (
                    id TEXT PRIMARY KEY,
                    category TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    embedding vector(384) NOT NULL
                );
                """
            )

    def _build(self) -> None:
        with self._conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM knowledge_base;")
            count = cur.fetchone()[0]
        if count > 0:
            return

        ids = [item["id"] for item in KNOWLEDGE_BASE]
        docs = [f"{item['title']}. {item['content']}" for item in KNOWLEDGE_BASE]
        embeddings = self._embedder.encode(docs).tolist()

        with self._conn.cursor() as cur:
            for item, doc, embedding in zip(KNOWLEDGE_BASE, docs, embeddings):
                cur.execute(
                    """
                    INSERT INTO knowledge_base (id, category, title, content, embedding)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING;
                    """,
                    (item["id"], item["category"], item["title"], item["content"], embedding),
                )
        logger.info("Vector store (PostgreSQL) seeded with %d documents", len(ids))

    def search(self, query: str, top_k: int = 3) -> List[Dict]:
        try:
            query_embedding = self._embedder.encode([query])[0].tolist()
            with self._conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT content, category, title, embedding <=> %s::vector AS distance
                    FROM knowledge_base
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s;
                    """,
                    (query_embedding, query_embedding, top_k),
                )
                rows = cur.fetchall()
            output = []
            for content, category, title, distance in rows:
                output.append({
                    "content": content,
                    "category": category,
                    "title": title,
                    "score": round(1 - distance, 3),
                })
            return output
        except Exception as exc:
            logger.error("Vector search failed: %s", exc)
            return []


vector_store = VectorStore()