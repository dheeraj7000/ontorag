"""Tests for document parser."""

import tempfile
from pathlib import Path

from backend.app.services.document_parser import parse_document


def test_parse_text_file():
    """Parsing a .txt file returns its content."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("Hello, this is a test document.\nSecond line.")
        f.flush()
        result = parse_document(Path(f.name))

    assert "Hello, this is a test document" in result
    assert "Second line" in result


def test_parse_markdown_strips_formatting():
    """Parsing markdown strips formatting but keeps text."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("# Title\n\n**Bold text** and [link](http://example.com)\n\n- list item")
        f.flush()
        result = parse_document(Path(f.name))

    assert "Title" in result
    assert "Bold text" in result
    assert "link" in result
    # Markdown symbols should be stripped
    assert "**" not in result
    assert "](http" not in result


def test_parse_html_extracts_text():
    """Parsing HTML extracts visible text content."""
    html = """<html><body>
    <h1>Page Title</h1>
    <p>Some content here.</p>
    <script>var x = 1;</script>
    </body></html>"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
        f.write(html)
        f.flush()
        result = parse_document(Path(f.name))

    assert "Page Title" in result
    assert "Some content here" in result
    # Script content should be stripped
    assert "var x" not in result


def test_parse_unsupported_raises():
    """Unsupported file type should raise ValueError."""
    import pytest

    with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
        f.write(b"data")
        f.flush()
        with pytest.raises(ValueError, match="Unsupported file type"):
            parse_document(Path(f.name))
