"""Unit tests for sequor.ai.document_parser.

Tests parser selection by file extension and parsed document structure.
Does not test actual file parsing (which requires real files), only the
factory function and ParsedDocument dataclass structure.
"""

import pytest

from sequor.ai.document_parser import (
    CSVParser,
    DOCXParser,
    DocumentParser,
    OCRParser,
    PDFParser,
    ParsedDocument,
    TXTParser,
    XLSXParser,
    get_parser_for_file,
)


# ---------------------------------------------------------------------------
# get_parser_for_file returns correct parser type
# ---------------------------------------------------------------------------


class TestGetParserForFile:
    """Tests for parser selection based on file extension."""

    @pytest.mark.parametrize(
        "filename, expected_class",
        [
            ("report.pdf", PDFParser),
            ("document.docx", DOCXParser),
            ("spreadsheet.xlsx", XLSXParser),
            ("legacy.xls", XLSXParser),
            ("data.csv", CSVParser),
            ("notes.txt", TXTParser),
            ("scan.png", OCRParser),
            ("photo.jpg", OCRParser),
            ("photo.jpeg", OCRParser),
        ],
    )
    def test_known_extensions(self, filename: str, expected_class: type):
        """Known file extensions return the correct parser type."""
        parser = get_parser_for_file(filename)
        assert isinstance(parser, expected_class)

    def test_uppercase_extension(self):
        """Case-insensitive extension matching."""
        parser = get_parser_for_file("REPORT.PDF")
        assert isinstance(parser, PDFParser)

    def test_unknown_extension_returns_txt_parser(self):
        """Unknown extensions fall back to TXTParser."""
        parser = get_parser_for_file("file.xyz")
        assert isinstance(parser, TXTParser)

    def test_no_extension_returns_txt_parser(self):
        """Files without an extension fall back to TXTParser."""
        parser = get_parser_for_file("README")
        assert isinstance(parser, TXTParser)

    def test_path_with_directory(self):
        """Full file paths are handled correctly."""
        parser = get_parser_for_file("/uploads/documents/quarterly.pdf")
        assert isinstance(parser, PDFParser)


# ---------------------------------------------------------------------------
# ParsedDocument structure
# ---------------------------------------------------------------------------


class TestParsedDocument:
    """Tests for the ParsedDocument dataclass."""

    def test_parsed_document_fields(self):
        """ParsedDocument has all expected fields with defaults."""
        doc = ParsedDocument(
            text="Hello world",
            metadata={"filename": "test.txt"},
        )

        assert doc.text == "Hello world"
        assert doc.metadata["filename"] == "test.txt"
        assert doc.pages_failed == 0
        assert doc.pages_total == 0

    def test_parsed_document_with_page_info(self):
        """ParsedDocument can carry page counts."""
        doc = ParsedDocument(
            text="Content",
            metadata={"filename": "report.pdf"},
            pages_failed=1,
            pages_total=10,
        )

        assert doc.pages_total == 10
        assert doc.pages_failed == 1

    def test_parsed_document_error_metadata(self):
        """Error conditions are represented via metadata."""
        doc = ParsedDocument(
            text="",
            metadata={"error": "pypdf not installed", "filename": "bad.pdf"},
        )

        assert doc.text == ""
        assert "error" in doc.metadata


# ---------------------------------------------------------------------------
# TXTParser (can be tested without external dependencies)
# ---------------------------------------------------------------------------


class TestTXTParser:
    """Tests for the plain text parser, which needs no external libraries."""

    async def test_parse_utf8_text(self):
        """TXTParser decodes UTF-8 content correctly."""
        parser = TXTParser()
        content = "Hello, world!".encode("utf-8")

        result = await parser.parse(content, "hello.txt")

        assert result.text == "Hello, world!"
        assert result.metadata["parser"] == "txt"
        assert result.metadata["filename"] == "hello.txt"

    async def test_parse_unicode_content(self):
        """TXTParser handles non-ASCII characters."""
        parser = TXTParser()
        content = "Café and résumé".encode("utf-8")

        result = await parser.parse(content, "unicode.txt")

        assert "Cafe" in result.text

    async def test_parse_empty_content(self):
        """TXTParser handles empty bytes."""
        parser = TXTParser()
        result = await parser.parse(b"", "empty.txt")

        assert result.text == ""

    async def test_parse_replaces_invalid_bytes(self):
        """TXTParser replaces invalid UTF-8 sequences gracefully."""
        parser = TXTParser()
        # Invalid UTF-8 byte sequence
        content = b"Hello \xff World"

        result = await parser.parse(content, "broken.txt")

        # Should not raise; replacement character is used
        assert "Hello" in result.text
        assert "World" in result.text


# ---------------------------------------------------------------------------
# CSVParser (can be tested with built-in csv module)
# ---------------------------------------------------------------------------


class TestCSVParser:
    """Tests for CSV parsing, which uses only the built-in csv module."""

    async def test_parse_csv_with_headers(self):
        """CSVParser extracts headers and rows."""
        parser = CSVParser()
        content = b"name,age\nAlice,30\nBob,25"

        result = await parser.parse(content, "people.csv")

        assert result.metadata["parser"] == "csv"
        assert result.metadata["row_count"] == 2
        assert result.metadata["column_count"] == 2
        assert "Alice" in result.text
        assert "Bob" in result.text

    async def test_parse_empty_csv(self):
        """CSVParser handles a CSV with only headers."""
        parser = CSVParser()
        content = b"name,age,email"

        result = await parser.parse(content, "empty.csv")

        assert result.metadata["row_count"] == 0
        assert "Columns:" in result.text
