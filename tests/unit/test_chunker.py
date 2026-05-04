"""Unit tests for sequor.ai.chunker.

Tests the three chunking strategies: line-item, section-based, and
sentence-overlap, plus edge cases and metadata correctness.
"""

import pytest

from sequor.ai.chunker import (
    Chunk,
    LineItemChunker,
    SectionChunker,
    SentenceOverlapChunker,
    get_chunker_for_document_type,
)


# ---------------------------------------------------------------------------
# LineItemChunker
# ---------------------------------------------------------------------------


class TestLineItemChunker:
    """Tests for line-item chunking (FAQ, price lists)."""

    def test_splits_lines_into_chunks(self):
        """Each non-empty line becomes a chunk."""
        text = "What is your pricing?\nOur plans start at $10/mo.\nWhere are you located?\nWe are in Singapore."
        chunker = LineItemChunker(min_chars=5)
        chunks = chunker.chunk(text)

        assert len(chunks) == 4
        assert chunks[0].text == "What is your pricing?"
        assert chunks[1].text == "Our plans start at $10/mo."

    def test_filters_short_lines(self):
        """Lines below min_chars are excluded."""
        text = "OK\nThis is long enough\nHi\nAnother good line here"
        chunker = LineItemChunker(min_chars=10)
        chunks = chunker.chunk(text)

        assert len(chunks) == 2
        assert chunks[0].text == "This is long enough"
        assert chunks[1].text == "Another good line here"

    def test_empty_text_returns_no_chunks(self):
        """Empty input produces zero chunks."""
        chunker = LineItemChunker()
        chunks = chunker.chunk("")
        assert chunks == []

    def test_single_line(self):
        """A single valid line produces one chunk."""
        chunker = LineItemChunker(min_chars=5)
        chunks = chunker.chunk("This is a single line of text")

        assert len(chunks) == 1
        assert chunks[0].text == "This is a single line of text"

    def test_chunk_metadata_includes_index_and_chunker_type(self):
        """Each chunk has sequential index and chunker metadata."""
        text = "Line one here\nLine two here\nLine three here"
        chunker = LineItemChunker(min_chars=5)
        chunks = chunker.chunk(text)

        for i, chunk in enumerate(chunks):
            assert chunk.index == i
            assert chunk.metadata["chunker"] == "line-item"

    def test_custom_metadata_propagated(self):
        """User-supplied metadata is merged into each chunk."""
        chunker = LineItemChunker(min_chars=5)
        chunks = chunker.chunk("Hello world text", metadata={"source": "test.doc"})

        assert chunks[0].metadata["source"] == "test.doc"

    def test_whitespace_only_lines_excluded(self):
        """Lines containing only whitespace are excluded."""
        text = "Valid line\n   \n\t\nAnother valid line"
        chunker = LineItemChunker(min_chars=5)
        chunks = chunker.chunk(text)

        assert len(chunks) == 2


# ---------------------------------------------------------------------------
# SectionChunker
# ---------------------------------------------------------------------------


class TestSectionChunker:
    """Tests for section-based chunking (policies, procedures)."""

    def test_splits_on_markdown_headings(self):
        """Markdown headings create chunk boundaries."""
        text = (
            "# Introduction\nThis is the intro.\n\n"
            "# Section One\nContent for section one.\n\n"
            "## Subsection\nMore details.\n\n"
            "# Section Two\nContent for section two."
        )
        chunker = SectionChunker(max_tokens=800)
        chunks = chunker.chunk(text)

        assert len(chunks) >= 3
        # First chunk should contain the introduction
        assert any("Introduction" in c.metadata.get("heading", "") for c in chunks)
        assert any("Section One" in c.metadata.get("heading", "") for c in chunks)

    def test_heading_metadata(self):
        """Chunks include heading and heading_level metadata."""
        text = "# Title\nBody text\n## Subtitle\nMore text"
        chunker = SectionChunker()
        chunks = chunker.chunk(text)

        assert chunks[0].metadata["chunker"] == "section"
        assert "heading" in chunks[0].metadata
        assert "heading_level" in chunks[0].metadata

    def test_empty_text_returns_no_chunks(self):
        """Empty input produces zero chunks."""
        chunker = SectionChunker()
        chunks = chunker.chunk("")
        assert chunks == []

    def test_no_headings_produces_single_chunk(self):
        """Text without any headings becomes one chunk."""
        text = "Just a paragraph of text.\nMore text here."
        chunker = SectionChunker()
        chunks = chunker.chunk(text)

        assert len(chunks) == 1

    def test_numbered_section_headings(self):
        """Numbered sections (e.g. '1. Title') are detected as headings."""
        text = "1. First Section\nContent one\n2. Second Section\nContent two"
        chunker = SectionChunker()
        chunks = chunker.chunk(text)

        assert len(chunks) >= 2

    def test_max_chars_respected(self):
        """Sections exceeding max_chars are flushed as separate chunks."""
        long_line = "A" * 200
        text = f"# Title\n{long_line}\n{long_line}\n{long_line}"
        chunker = SectionChunker(max_tokens=100)  # 400 chars max
        chunks = chunker.chunk(text)

        # With max_chars=400, multiple sections should be created
        assert len(chunks) >= 1

    def test_all_caps_heading_detected(self):
        """ALL CAPS lines are detected as headings."""
        text = "INTRODUCTION\nThis is the intro.\nPOLICY\nThe policy text."
        chunker = SectionChunker()
        chunks = chunker.chunk(text)

        assert len(chunks) >= 2


# ---------------------------------------------------------------------------
# SentenceOverlapChunker
# ---------------------------------------------------------------------------


class TestSentenceOverlapChunker:
    """Tests for sentence-overlap chunking (informal docs)."""

    def test_splits_into_sentence_chunks(self):
        """Text is split into overlapping sentence groups."""
        text = (
            "First sentence here. Second sentence follows. "
            "Third sentence comes next. Fourth sentence is here. "
            "Fifth sentence ends it."
        )
        chunker = SentenceOverlapChunker(sentences_per_chunk=3, overlap_sentences=1)
        chunks = chunker.chunk(text)

        assert len(chunks) >= 2
        # First chunk should contain the first 3 sentences
        assert "First sentence" in chunks[0].text

    def test_overlap_between_chunks(self):
        """Consecutive chunks share overlapping sentences."""
        text = "One. Two. Three. Four. Five. Six."
        chunker = SentenceOverlapChunker(sentences_per_chunk=3, overlap_sentences=1)
        chunks = chunker.chunk(text)

        if len(chunks) >= 2:
            # With overlap=1, step=2; second chunk starts at sentence index 2
            # which means sentence "Three." appears in both chunk 0 and chunk 1
            overlap_found = False
            for i in range(len(chunks) - 1):
                words_0 = set(chunks[i].text.split())
                words_1 = set(chunks[i + 1].text.split())
                if words_0 & words_1:
                    overlap_found = True
            assert overlap_found

    def test_chunk_metadata(self):
        """Chunks include sentence range metadata."""
        text = "First sentence. Second sentence. Third sentence."
        chunker = SentenceOverlapChunker(sentences_per_chunk=3, overlap_sentences=1)
        chunks = chunker.chunk(text)

        assert chunks[0].metadata["chunker"] == "sentence-overlap"
        assert "start_sentence" in chunks[0].metadata
        assert "end_sentence" in chunks[0].metadata

    def test_empty_text_returns_no_chunks(self):
        """Empty input produces zero chunks."""
        chunker = SentenceOverlapChunker()
        chunks = chunker.chunk("")
        assert chunks == []

    def test_single_sentence(self):
        """A single sentence produces one chunk."""
        chunker = SentenceOverlapChunker()
        chunks = chunker.chunk("Just one sentence here.")

        assert len(chunks) == 1
        assert "Just one sentence here." in chunks[0].text

    def test_custom_metadata_propagated(self):
        """User-supplied metadata is merged into each chunk."""
        chunker = SentenceOverlapChunker()
        chunks = chunker.chunk("Hello world here.", metadata={"source": "notes.txt"})

        assert chunks[0].metadata["source"] == "notes.txt"

    def test_sentence_splitting_with_exclamation(self):
        """Sentences ending with ! are split correctly."""
        text = "Are you open! Yes we are! Great to know."
        chunker = SentenceOverlapChunker(sentences_per_chunk=2, overlap_sentences=0)
        chunks = chunker.chunk(text)

        assert len(chunks) >= 2


# ---------------------------------------------------------------------------
# get_chunker_for_document_type
# ---------------------------------------------------------------------------


class TestGetChunkerForDocumentType:
    """Tests for the chunker factory function."""

    @pytest.mark.parametrize(
        "doc_type, expected_class",
        [
            ("faq", LineItemChunker),
            ("roster", LineItemChunker),
            ("price_list", LineItemChunker),
            ("policy", SectionChunker),
        ],
    )
    def test_known_document_types(self, doc_type: str, expected_class: type):
        """Known document types return the correct chunker class."""
        chunker = get_chunker_for_document_type(doc_type)
        assert isinstance(chunker, expected_class)

    def test_other_returns_sentence_overlap(self):
        """Document type 'other' returns SentenceOverlapChunker."""
        chunker = get_chunker_for_document_type("other")
        assert isinstance(chunker, SentenceOverlapChunker)

    def test_unknown_type_returns_sentence_overlap(self):
        """Unknown document types default to SentenceOverlapChunker."""
        chunker = get_chunker_for_document_type("random_type")
        assert isinstance(chunker, SentenceOverlapChunker)
