"""Long-term semantic memory (PGVector + FastEmbed). Every record is scoped to one user."""
import logging
import threading

from app.db.postgres import PSYCOPG_URL

logger = logging.getLogger(__name__)

_vector_store = None
_init_failed = False
_lock = threading.Lock()


class MemoryUnavailable(RuntimeError):
    pass


def _get_store():
    """Builds the store on first use: loading the embedding model at import slowed every startup."""
    global _vector_store, _init_failed
    if _vector_store is not None:
        return _vector_store
    if not PSYCOPG_URL or _init_failed:
        raise MemoryUnavailable("Long-term memory requires a Postgres DATABASE_URL with pgvector.")
    with _lock:
        if _vector_store is None:
            try:
                from langchain_community.embeddings import FastEmbedEmbeddings
                from langchain_postgres import PGVector

                store = PGVector(
                    embeddings=FastEmbedEmbeddings(model_name="BAAI/bge-small-en-v1.5"),
                    collection_name="agent_memory",
                    connection=PSYCOPG_URL.replace("postgresql://", "postgresql+psycopg://", 1),
                    use_jsonb=True,
                )
                store.create_tables_if_not_exists()
                _vector_store = store
            except Exception as e:
                _init_failed = True
                logger.error(f"Failed to initialize PGVector: {e}")
                raise MemoryUnavailable(f"Long-term memory is unavailable: {e}") from e
    return _vector_store


def add_to_memory(text: str, user_id: str, metadata: dict | None = None) -> None:
    """Stores a snippet for `user_id`. Raises on failure so callers never report a false success."""
    metadata = dict(metadata or {"source": "user_input"})
    metadata["user_id"] = str(user_id)
    _get_store().add_texts(texts=[text], metadatas=[metadata])


def search_memory(query: str, user_id: str, k: int = 3) -> list[str]:
    """Returns the `k` most similar snippets belonging to `user_id` only."""
    results = _get_store().similarity_search(query, k=k, filter={"user_id": {"$eq": str(user_id)}})
    return [doc.page_content for doc in results]
