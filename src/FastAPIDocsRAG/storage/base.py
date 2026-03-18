"""
Abstract base class for storage backends.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from langchain_core.documents import Document


class StorageBackend(ABC):
    """Abstract base class for storage backends."""
    
    @abstractmethod
    def save_chunks(self, chunks: List[Document], file_path: str) -> None:
        """
        Save document chunks to storage.
        
        Args:
            chunks: List of document chunks
            file_path: Storage file path
        """
        pass
    
    @abstractmethod
    def load_chunks(self, file_path: str) -> List[Document]:
        """
        Load document chunks from storage.
        
        Args:
            file_path: Storage file path
            
        Returns:
            List of document chunks
        """
        pass
    
    @abstractmethod
    def save_metadata(self, metadata: Dict[str, Any], file_path: str) -> None:
        """
        Save metadata to storage.
        
        Args:
            metadata: Metadata dictionary
            file_path: Storage file path
        """
        pass
    
    @abstractmethod
    def load_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Load metadata from storage.
        
        Args:
            file_path: Storage file path
            
        Returns:
            Metadata dictionary
        """
        pass
    
    @abstractmethod
    def exists(self, file_path: str) -> bool:
        """
        Check if file exists in storage.
        
        Args:
            file_path: Storage file path
            
        Returns:
            True if file exists, False otherwise
        """
        pass
