"""
Custom exceptions for the FastAPIDocsRAG system.
"""


class FastAPIDocsRAGException(Exception):
    """Base exception for all FastAPIDocsRAG errors."""
    pass


class ConfigurationError(FastAPIDocsRAGException):
    """Raised when there's an error in configuration."""
    pass


class PipelineError(FastAPIDocsRAGException):
    """Raised when there's an error in the pipeline processing."""
    pass


class StorageError(FastAPIDocsRAGException):
    """Raised when there's an error in storage operations."""
    pass


class EmbeddingError(FastAPIDocsRAGException):
    """Raised when there's an error in embedding generation."""
    pass


class ProcessingError(FastAPIDocsRAGException):
    """Raised when there's an error in document processing."""
    pass
