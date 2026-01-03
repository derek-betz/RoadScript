"""Text chunking utilities for retrieval indexing."""

from typing import Iterable, List


def chunk_text(text: str, chunk_size: int = 700, overlap: int = 100) -> List[str]:
    """Split text into word-based chunks with overlap."""
    words = text.split()
    if not words:
        return []

    chunks: List[str] = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk_words = words[start:end]
        chunks.append(" ".join(chunk_words))
        if end == len(words):
            break
        start = max(0, end - overlap)
    return chunks


def chunk_paragraphs(paragraphs: Iterable[str], chunk_size: int = 700) -> List[str]:
    """Chunk pre-split paragraphs into word-based blocks."""
    chunks: List[str] = []
    current: List[str] = []
    current_words = 0
    for paragraph in paragraphs:
        words = paragraph.split()
        if not words:
            continue
        if current_words + len(words) > chunk_size and current:
            chunks.append(" ".join(current))
            current = []
            current_words = 0
        current.append(paragraph)
        current_words += len(words)
    if current:
        chunks.append(" ".join(current))
    return chunks
