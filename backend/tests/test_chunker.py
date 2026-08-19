"""Tests for the text chunker."""

from backend.app.services.chunker import chunk_text


def test_empty_text_returns_no_chunks():
    """Empty text should produce no chunks."""
    assert chunk_text("") == []
    assert chunk_text("   ") == []


def test_short_text_single_chunk():
    """Short text that fits in one chunk produces a single chunk."""
    text = "FastAPI is a modern web framework for building APIs with Python."
    chunks = chunk_text(text, chunk_size=500, overlap=50)
    assert len(chunks) == 1
    assert chunks[0].chunk_index == 0
    assert chunks[0].text == text


def test_long_text_multiple_chunks():
    """Long text should be split into multiple overlapping chunks."""
    # Create a text that's clearly longer than one chunk
    sentences = [f"Sentence number {i} with enough words to count as tokens." for i in range(100)]
    text = " ".join(sentences)

    chunks = chunk_text(text, chunk_size=100, overlap=20)
    assert len(chunks) > 1

    # Verify chunk indices are sequential
    for i, chunk in enumerate(chunks):
        assert chunk.chunk_index == i

    # Verify all chunks have content
    for chunk in chunks:
        assert len(chunk.text) > 0
        assert chunk.token_count > 0


def test_chunk_overlap():
    """Consecutive chunks should overlap (share some content)."""
    sentences = [f"This is sentence {i} in the document about AI systems." for i in range(50)]
    text = " ".join(sentences)

    chunks = chunk_text(text, chunk_size=50, overlap=15)

    if len(chunks) >= 2:
        # Check there's overlap by looking for shared words
        words_first = set(chunks[0].text.split()[-10:])
        words_second = set(chunks[1].text.split()[:10])
        # There should be some shared content due to overlap
        assert len(words_first & words_second) > 0


def test_chunk_metadata():
    """Chunks should have correct metadata."""
    text = "First sentence. Second sentence. Third sentence."
    chunks = chunk_text(text, chunk_size=500, overlap=10)
    assert chunks[0].start_char == 0
    assert chunks[0].chunk_index == 0
