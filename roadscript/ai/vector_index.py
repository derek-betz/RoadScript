"""Vector index helper built on ChromaDB."""

from __future__ import annotations

from dataclasses import asdict
import json
import os
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from roadscript.ai.embeddings import EmbeddingConfig, config_from_env, get_embedding_function


class VectorIndex:
    """Persistent vector index wrapper for INDOT documents."""

    def __init__(
        self,
        persist_path: Path,
        collection_name: str = "indot_standards",
        embedding_config: Optional[EmbeddingConfig] = None,
    ) -> None:
        try:
            import chromadb  # type: ignore
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise ImportError(
                "chromadb is required for vector indexing. Install it to enable RAG."
            ) from exc
        self.persist_path = persist_path
        self.collection_name = collection_name
        self.embedding_config = embedding_config or config_from_env()
        self._client = chromadb.PersistentClient(path=str(self.persist_path))
        self._collection = None

    @property
    def collection(self):
        if self._collection is None:
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=get_embedding_function(self.embedding_config),
            )
        return self._collection

    def reset(self) -> None:
        """Delete and recreate the collection."""
        try:
            self._client.delete_collection(self.collection_name)
        except ValueError:
            pass
        self._collection = None
        _ = self.collection

    def add_documents(
        self,
        texts: Iterable[str],
        metadatas: Iterable[Dict[str, object]],
        ids: Iterable[str],
    ) -> None:
        self.collection.add(documents=list(texts), metadatas=list(metadatas), ids=list(ids))

    def query(self, query_text: str, top_k: int = 5) -> Dict[str, List[object]]:
        return self.collection.query(query_texts=[query_text], n_results=top_k)

    def save_config(self) -> None:
        config_path = self.persist_path / "index_config.json"
        embedding = asdict(self.embedding_config)
        embedding.pop("api_key", None)
        config_path.write_text(
            json.dumps(
                {
                    "collection_name": self.collection_name,
                    "embedding": embedding,
                },
                indent=2,
            ),
            encoding="utf-8",
        )


def load_index_config(persist_path: Path) -> Optional[EmbeddingConfig]:
    config_path = persist_path / "index_config.json"
    if not config_path.exists():
        return None
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    embedding = payload.get("embedding", {})
    if not embedding:
        return None
    return EmbeddingConfig(
        provider=embedding.get("provider", "sentence-transformer"),
        model=embedding.get("model", "all-MiniLM-L6-v2"),
        api_key=embedding.get("api_key") or os.getenv("OPENAI_API_KEY"),
    )
