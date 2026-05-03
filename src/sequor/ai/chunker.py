"""Text chunking strategies for document processing.

Three strategies:
- Line-item: For FAQ, price lists (discrete Q+A pairs or line items)
- Section-based: For policy, procedures (chunk boundaries at H1/H2 headings)
- Sentence-overlap: For informal notes, chat exports (3-sentence chunks with overlap)
"""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import structlog

logger = structlog.get_logger()


@dataclass
class Chunk:
    """A text chunk with metadata."""

    text: str
    index: int
    metadata: dict[str, Any]


class ChunkingStrategy(ABC):
    """Base class for chunking strategies."""

    @abstractmethod
    def chunk(self, text: str, metadata: dict[str, Any] | None = None) -> list[Chunk]:
        """Split text into chunks.

        Args:
            text: The text to chunk
            metadata: Additional metadata to attach to each chunk

        Returns:
            List of Chunk objects
        """
        ...


class LineItemChunker(ChunkingStrategy):
    """Line-item chunking for FAQs and price lists.

    Treats each Q+A pair or line item as a discrete chunk.
    """

    def __init__(self, min_chars: int = 10) -> None:
        """Initialize the line-item chunker.

        Args:
            min_chars: Minimum characters for a line to be considered a chunk
        """
        self.min_chars = min_chars

    def chunk(self, text: str, metadata: dict[str, Any] | None = None) -> list[Chunk]:
        """Split text by lines, treating each non-empty line as a chunk."""
        meta = metadata or {}
        chunks = []
        chunk_index = 0

        lines = text.split("\n")

        for line in lines:
            stripped = line.strip()
            if len(stripped) >= self.min_chars:
                chunks.append(
                    Chunk(
                        text=stripped,
                        index=chunk_index,
                        metadata={**meta, "chunker": "line-item"},
                    )
                )
                chunk_index += 1

        logger.info(
            "chunker.line_item.ok",
            total_lines=len(lines),
            chunks_created=len(chunks),
        )
        return chunks


class SectionChunker(ChunkingStrategy):
    """Section-based chunking for policies and procedures.

    Uses heading patterns to identify section boundaries.
    Preserves hierarchical structure in chunk metadata.
    """

    HEADING_PATTERNS = [
        r"^#{1,3}\s+(.+)$",  # Markdown headings (# ## ###)
        r"^([A-Z][A-Z\s]{5,})$",  # ALL CAPS headings
        r"^(\d+\.\s+.+)$",  # Numbered sections (1. 2. 3.)
        r"^([A-Z][a-z]+(\s+[A-Z][a-z]+){0,3}:)$",  # Title Case headings with colon
    ]

    def __init__(self, max_tokens: int = 800) -> None:
        """Initialize the section chunker.

        Args:
            max_tokens: Maximum tokens per chunk (approximate, 4 chars/token)
        """
        self.max_tokens = max_tokens
        self.max_chars = max_tokens * 4

    def _is_heading(self, line: str) -> bool:
        """Check if a line is a heading."""
        stripped = line.strip()
        return any(re.match(pattern, stripped) for pattern in self.HEADING_PATTERNS)

    def chunk(self, text: str, metadata: dict[str, Any] | None = None) -> list[Chunk]:
        """Split text by sections based on headings."""
        meta = metadata or {}
        chunks = []
        chunk_index = 0

        lines = text.split("\n")
        current_section_lines = []
        current_heading = ""
        current_heading_level = 0

        def _flush_section() -> None:
            nonlocal current_section_lines, chunk_index, chunks
            if current_section_lines:
                section_text = "\n".join(current_section_lines).strip()
                if section_text:
                    chunks.append(
                        Chunk(
                            text=section_text,
                            index=chunk_index,
                            metadata={
                                **meta,
                                "chunker": "section",
                                "heading": current_heading,
                                "heading_level": current_heading_level,
                            },
                        )
                    )
                    chunk_index += 1
                current_section_lines = []

        for line in lines:
            if self._is_heading(line):
                _flush_section()
                stripped = line.strip()
                heading_match = re.match(r"^(#+)\s+(.+)$", stripped)
                if heading_match:
                    current_heading_level = len(heading_match.group(1))
                    current_heading = heading_match.group(2)
                else:
                    current_heading = stripped.lstrip("0123456789. ")
                    current_heading_level = 1
                current_section_lines = [line]
            else:
                if len("\n".join(current_section_lines + [line])) <= self.max_chars:
                    current_section_lines.append(line)
                else:
                    _flush_section()
                    current_section_lines = [line]

        _flush_section()

        logger.info(
            "chunker.section.ok",
            total_lines=len(lines),
            chunks_created=len(chunks),
        )
        return chunks


class SentenceOverlapChunker(ChunkingStrategy):
    """Sentence-level chunking with overlap for informal content.

    Creates chunks of N sentences with M sentence overlap.
    Better recall on informal content like chat exports.
    """

    SENTENCE_ENDINGS = re.compile(r"(?<=[.!?])\s+")

    def __init__(self, sentences_per_chunk: int = 3, overlap_sentences: int = 1) -> None:
        """Initialize the sentence overlap chunker.

        Args:
            sentences_per_chunk: Number of sentences per chunk
            overlap_sentences: Number of sentences to overlap between chunks
        """
        self.sentences_per_chunk = sentences_per_chunk
        self.overlap_sentences = overlap_sentences

    def _split_sentences(self, text: str) -> list[str]:
        """Split text into sentences."""
        parts = self.SENTENCE_ENDINGS.split(text)
        sentences = []
        current = ""

        for part in parts:
            current += part
            if current.strip().endswith((".", "!", "?")):
                sentences.append(current.strip())
                current = ""

        if current.strip():
            sentences.append(current.strip())

        return [s for s in sentences if s]

    def chunk(self, text: str, metadata: dict[str, Any] | None = None) -> list[Chunk]:
        """Split text into overlapping sentence chunks."""
        meta = metadata or {}
        chunks = []
        chunk_index = 0

        sentences = self._split_sentences(text)

        if not sentences:
            return chunks

        step = max(1, self.sentences_per_chunk - self.overlap_sentences)

        for i in range(0, len(sentences), step):
            chunk_sentences = sentences[i : i + self.sentences_per_chunk]
            if len(chunk_sentences) >= 1:
                chunk_text = " ".join(chunk_sentences)
                chunks.append(
                    Chunk(
                        text=chunk_text,
                        index=chunk_index,
                        metadata={
                            **meta,
                            "chunker": "sentence-overlap",
                            "start_sentence": i,
                            "end_sentence": i + len(chunk_sentences) - 1,
                        },
                    )
                )
                chunk_index += 1

            if i + self.sentences_per_chunk >= len(sentences):
                break

        logger.info(
            "chunker.sentence_overlap.ok",
            total_sentences=len(sentences),
            chunks_created=len(chunks),
        )
        return chunks


def get_chunker_for_document_type(
    document_type: str,
) -> ChunkingStrategy:
    """Get the appropriate chunking strategy for a document type.

    Args:
        document_type: One of 'faq', 'roster', 'price_list', 'policy', 'other'

    Returns:
        Appropriate ChunkingStrategy instance
    """
    strategies = {
        "faq": LineItemChunker(),
        "roster": LineItemChunker(),
        "price_list": LineItemChunker(),
        "policy": SectionChunker(max_tokens=800),
        "other": SentenceOverlapChunker(sentences_per_chunk=3, overlap_sentences=1),
    }

    strategy = strategies.get(document_type, SentenceOverlapChunker())
    logger.debug(
        "chunker.selected",
        document_type=document_type,
        strategy=type(strategy).__name__,
    )
    return strategy
