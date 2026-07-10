"""AI module for Sequor.

Exports:
- OllamaClient: Local LLM and embedding generation (Ollama)
- DeepSeekClient: Cloud LLM generation (DeepSeek, OpenAI-compatible API)
- get_llm_client: Provider-agnostic client factory (returns OllamaClient or DeepSeekClient)
- DocumentParser: Document parsing for various formats
- Chunking strategies: Line-item, section, sentence-overlap
- VectorStore: Hybrid vector + BM25 retrieval
- RAGPipeline: Retrieval-augmented generation
- DocumentIngester: Document ingestion pipeline
- LearningLoop: Capture human answers from escalations
- MessageClassifier: Message classification engine
- ResponseGenerator: Response generation with confidence
"""

from sequor.ai.chunker import (
    Chunk,
    ChunkingStrategy,
    LineItemChunker,
    SectionChunker,
    SentenceOverlapChunker,
    get_chunker_for_document_type,
)
from sequor.ai.classifier import (
    ClassificationResult,
    MessageCategory,
    MessageClassifier,
    MessageUrgency,
)
from sequor.ai.client import DeepSeekClient, OllamaClient, get_llm_client, get_ollama_client
from sequor.ai.document_parser import (
    CSVParser,
    DocumentParser,
    DOCXParser,
    OCRParser,
    ParsedDocument,
    PDFParser,
    TXTParser,
    XLSXParser,
    get_parser_for_file,
)
from sequor.ai.ingestion import DocumentIngester, IngestionResult
from sequor.ai.learning import LearnedAnswerRecord, LearningLoop
from sequor.ai.rag_pipeline import RAGPipeline, RetrievalResult, SynthesisResult
from sequor.ai.response import ResponseGenerator, ResponseResult
from sequor.ai.vector_store import SearchResult, VectorStore

__all__ = [
    # Client
    "OllamaClient",
    "DeepSeekClient",
    "get_ollama_client",
    "get_llm_client",
    # Document parsing
    "DocumentParser",
    "ParsedDocument",
    "PDFParser",
    "DOCXParser",
    "XLSXParser",
    "CSVParser",
    "TXTParser",
    "OCRParser",
    "get_parser_for_file",
    # Chunking
    "Chunk",
    "ChunkingStrategy",
    "LineItemChunker",
    "SectionChunker",
    "SentenceOverlapChunker",
    "get_chunker_for_document_type",
    # Vector store
    "VectorStore",
    "SearchResult",
    # RAG
    "RAGPipeline",
    "RetrievalResult",
    "SynthesisResult",
    # Ingestion
    "DocumentIngester",
    "IngestionResult",
    # Learning
    "LearningLoop",
    "LearnedAnswerRecord",
    # Classification
    "MessageClassifier",
    "MessageCategory",
    "MessageUrgency",
    "ClassificationResult",
    # Response
    "ResponseGenerator",
    "ResponseResult",
]
