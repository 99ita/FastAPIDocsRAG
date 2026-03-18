"""
FastAPIDocsRAG - Enhanced Technical Documentation RAG System

A modular, scalable RAG pipeline for technical documentation with support for:
- Document ingestion and processing
- Code reference extraction
- Metadata enhancement from MkDocs
- Multiple storage backends
- Embedding generation
- Query and retrieval capabilities
"""

__version__ = "0.1.0"
__author__ = "FastAPIDocsRAG Team"

from .core.pipeline import RAGPipeline
from .core.config import Config

__all__ = ["RAGPipeline", "Config"]
