"""
Text Chunker — splits documents into overlapping chunks for extraction.

Uses tiktoken for accurate token counting (same tokenizer as GPT models).
Chunk size: 500 tokens with 50 token overlap.
"""

import logging
from dataclasses import dataclass
from typing import List

logger = logging.getLogger(__name__)

# Default chunking parameters
DEFAULT_CHUNK_SIZE = 500  # tokens
DEFAULT_OVERLAP = 50  # tokens


@dataclass
class TextChunk:
    """A chunk of text with metadata."""

    text: str
    chunk_index: int
    start_char: int
    end_char: int
    token_count: int


def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
) -> List[TextChunk]:
    """
    Split text into overlapping chunks based on token count.

    Strategy:
    1. Split text into sentences
    2. Group sentences into chunks of ~chunk_size tokens
    3. Overlap by ~overlap tokens between consecutive chunks
    """
    if not text.strip():
        return []

    try:
        import tiktoken

        encoder = tiktoken.get_encoding("cl100k_base")
    except ImportError:
        # Fallback: approximate tokens as words / 0.75
        logger.warning("tiktoken not available, using word-based approximation")
        encoder = None

    sentences = _split_sentences(text)
    if not sentences:
        return []

    chunks: List[TextChunk] = []
    current_sentences: List[str] = []
    current_tokens = 0
    chunk_index = 0
    char_offset = 0

    for sentence in sentences:
        sentence_tokens = _count_tokens(sentence, encoder)

        # If adding this sentence exceeds chunk size, finalize current chunk
        if current_tokens + sentence_tokens > chunk_size and current_sentences:
            chunk_text_str = " ".join(current_sentences)
            chunks.append(
                TextChunk(
                    text=chunk_text_str,
                    chunk_index=chunk_index,
                    start_char=char_offset,
                    end_char=char_offset + len(chunk_text_str),
                    token_count=current_tokens,
                )
            )
            chunk_index += 1

            # Calculate overlap: keep last N tokens worth of sentences
            overlap_sentences: List[str] = []
            overlap_tokens = 0
            for s in reversed(current_sentences):
                s_tokens = _count_tokens(s, encoder)
                if overlap_tokens + s_tokens > overlap:
                    break
                overlap_sentences.insert(0, s)
                overlap_tokens += s_tokens

            char_offset += len(chunk_text_str) - len(" ".join(overlap_sentences))
            current_sentences = overlap_sentences
            current_tokens = overlap_tokens

        current_sentences.append(sentence)
        current_tokens += sentence_tokens

    # Don't forget the last chunk
    if current_sentences:
        chunk_text_str = " ".join(current_sentences)
        chunks.append(
            TextChunk(
                text=chunk_text_str,
                chunk_index=chunk_index,
                start_char=char_offset,
                end_char=char_offset + len(chunk_text_str),
                token_count=current_tokens,
            )
        )

    logger.info(
        f"Chunked text into {len(chunks)} chunks "
        f"(avg {sum(c.token_count for c in chunks) // max(len(chunks), 1)} tokens/chunk)"
    )
    return chunks


def _split_sentences(text: str) -> List[str]:
    """Split text into sentences using simple heuristics."""
    import re

    # Split on sentence boundaries
    # Handles: period, question mark, exclamation, newlines
    raw_sentences = re.split(r"(?<=[.!?])\s+|\n{2,}", text)

    # Filter empty and whitespace-only
    sentences = [s.strip() for s in raw_sentences if s.strip()]
    return sentences


def _count_tokens(text: str, encoder) -> int:
    """Count tokens in text using tiktoken or word approximation."""
    if encoder is not None:
        return len(encoder.encode(text))
    # Rough approximation: 1 token ≈ 4 chars for English
    return max(1, len(text) // 4)
