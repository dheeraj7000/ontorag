"""
Document Parser — extracts plain text from PDF, Markdown, HTML, and TXT files.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def parse_document(file_path: Path) -> str:
    """
    Parse a document and return its plain text content.

    Supports: .pdf, .md, .html, .txt
    """
    ext = file_path.suffix.lower()

    if ext == ".pdf":
        return _parse_pdf(file_path)
    elif ext == ".md":
        return _parse_markdown(file_path)
    elif ext == ".html":
        return _parse_html(file_path)
    elif ext == ".txt":
        return _parse_text(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def _parse_pdf(file_path: Path) -> str:
    """Extract text from a PDF file."""
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(file_path))
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text.strip())

        full_text = "\n\n".join(pages)
        logger.info(f"Parsed PDF: {len(reader.pages)} pages, {len(full_text)} chars")
        return full_text
    except ImportError:
        raise RuntimeError("pypdf is required for PDF parsing. Install: pip install pypdf")


def _parse_markdown(file_path: Path) -> str:
    """Extract plain text from a Markdown file (strip formatting)."""
    import re

    raw = file_path.read_text(encoding="utf-8")

    # Strip markdown formatting but preserve structure
    # Remove code blocks
    text = re.sub(r"```[\s\S]*?```", "", raw)
    # Remove inline code
    text = re.sub(r"`[^`]+`", "", text)
    # Remove images
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
    # Convert links to just text
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    # Remove headers markers but keep text
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    # Remove bold/italic markers
    text = re.sub(r"\*{1,3}([^*]+)\*{1,3}", r"\1", text)
    text = re.sub(r"_{1,3}([^_]+)_{1,3}", r"\1", text)
    # Remove horizontal rules
    text = re.sub(r"^[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)
    # Clean up extra whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)

    logger.info(f"Parsed Markdown: {len(text)} chars")
    return text.strip()


def _parse_html(file_path: Path) -> str:
    """Extract plain text from an HTML file."""
    try:
        from bs4 import BeautifulSoup

        raw = file_path.read_text(encoding="utf-8")
        soup = BeautifulSoup(raw, "html.parser")

        # Remove script and style elements
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)
        logger.info(f"Parsed HTML: {len(text)} chars")
        return text
    except ImportError:
        raise RuntimeError(
            "beautifulsoup4 is required for HTML parsing. Install: pip install beautifulsoup4"
        )


def _parse_text(file_path: Path) -> str:
    """Read a plain text file."""
    text = file_path.read_text(encoding="utf-8")
    logger.info(f"Parsed TXT: {len(text)} chars")
    return text
