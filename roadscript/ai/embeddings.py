"""Embedding configuration helpers for vector indexing."""

from dataclasses import asdict, dataclass
import logging
import os
from typing import Dict, List, Optional

try:
    from chromadb.utils import embedding_functions
except ImportError as exc:  # pragma: no cover - exercised in runtime
    embedding_functions = None
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None

LOG = logging.getLogger(__name__)


@dataclass(frozen=True)
class EmbeddingConfig:
    """Embedding provider configuration."""

    provider: str
    model: str
    api_key: Optional[str] = None

    def as_dict(self) -> Dict[str, object]:
        return asdict(self)


def config_from_env() -> EmbeddingConfig:
    """Select embedding configuration based on environment variables."""
    provider_override_raw = os.getenv("ROADSCRIPT_EMBEDDING_PROVIDER")
    provider_override = _normalize_provider(provider_override_raw)
    if provider_override_raw and provider_override is None:
        LOG.warning(
            "Unknown ROADSCRIPT_EMBEDDING_PROVIDER=%s; using default provider selection.",
            provider_override_raw,
        )

    if provider_override == "openai":
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            return EmbeddingConfig(
                provider="openai",
                model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
                api_key=openai_key,
            )
        LOG.warning(
            "ROADSCRIPT_EMBEDDING_PROVIDER=openai set but OPENAI_API_KEY is missing; "
            "falling back to local embeddings."
        )

    if provider_override == "sentence-transformer":
        return EmbeddingConfig(
            provider="sentence-transformer",
            model=os.getenv("LOCAL_EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
            api_key=None,
        )

    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        return EmbeddingConfig(
            provider="openai",
            model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
            api_key=openai_key,
        )
    return EmbeddingConfig(
        provider="sentence-transformer",
        model=os.getenv("LOCAL_EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
        api_key=None,
    )


def _normalize_provider(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    normalized = value.strip().lower()
    if normalized in {"openai", "sentence-transformer"}:
        return normalized
    if normalized in {"sentence_transformer", "local", "local-embeddings"}:
        return "sentence-transformer"
    return None


def get_embedding_function(config: EmbeddingConfig):
    """Return a Chroma embedding function from config."""
    if embedding_functions is None:
        raise ImportError(
            "chromadb embedding_functions unavailable."
        ) from _IMPORT_ERROR

    if config.provider == "openai":
        return _OpenAIEmbeddingFunctionV1(
            api_key=config.api_key,
            model_name=config.model,
        )
    if config.provider == "sentence-transformer":
        return embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=config.model,
        )
    raise ValueError(f"Unsupported embedding provider: {config.provider}")


class _OpenAIEmbeddingFunctionV1:
    """OpenAI embeddings adapter compatible with openai>=1.0."""

    def __init__(self, api_key: Optional[str], model_name: str) -> None:
        from openai import OpenAI

        self._client = OpenAI(api_key=api_key)
        self._model = model_name
        self._batch_size = _parse_batch_size(
            os.getenv("OPENAI_EMBEDDING_BATCH_SIZE"),
            default=100,
        )

    def __call__(self, input: List[str]) -> List[List[float]]:
        if isinstance(input, str):
            input = [input]
        if not input:
            return []
        embeddings: List[List[float]] = []
        for start in range(0, len(input), self._batch_size):
            batch = input[start:start + self._batch_size]
            response = self._client.embeddings.create(
                model=self._model,
                input=batch,
            )
            embeddings.extend(item.embedding for item in response.data)
        return embeddings


def _parse_batch_size(value: Optional[str], default: int) -> int:
    if not value:
        return default
    try:
        parsed = int(value)
    except ValueError:
        LOG.warning("Invalid OPENAI_EMBEDDING_BATCH_SIZE=%s; using %s.", value, default)
        return default
    if parsed <= 0:
        LOG.warning("OPENAI_EMBEDDING_BATCH_SIZE must be positive; using %s.", default)
        return default
    return parsed
