"""
Local file system storage implementation.
"""

import json
from typing import List, Dict, Any
from pathlib import Path
from langchain_core.documents import Document

from .base import StorageBackend
from ..core.exceptions import StorageError


class LocalStorage(StorageBackend):
    """Local file system storage backend."""
    
    def __init__(self, base_path: str = "./"):
        """
        Initialize local storage.
        
        Args:
            base_path: Base directory for storage
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def save_chunks(self, chunks: List[Document], file_path: str) -> None:
        """
        Save document chunks to JSONL file.
        
        Args:
            chunks: List of document chunks
            file_path: Storage file path
        """
        full_path = self.base_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(full_path, 'w', encoding='utf-8') as f:
                for chunk in chunks:
                    chunk_data = {
                        'page_content': chunk.page_content,
                        'metadata': chunk.metadata
                    }
                    f.write(json.dumps(chunk_data, ensure_ascii=False) + '\n')
        except Exception as e:
            raise StorageError(f"Failed to save chunks to {full_path}: {e}")
    
    def load_chunks(self, file_path: str) -> List[Document]:
        """
        Load document chunks from JSONL file.
        
        Args:
            file_path: Storage file path
            
        Returns:
            List of document chunks
        """
        full_path = self.base_path / file_path
        
        if not full_path.exists():
            raise StorageError(f"File not found: {full_path}")
        
        chunks = []
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        chunk_data = json.loads(line)
                        chunk = Document(
                            page_content=chunk_data['page_content'],
                            metadata=chunk_data['metadata']
                        )
                        chunks.append(chunk)
        except Exception as e:
            raise StorageError(f"Failed to load chunks from {full_path}: {e}")
        
        return chunks
    
    def save_metadata(self, metadata: Dict[str, Any], file_path: str) -> None:
        """
        Save metadata to JSON file.
        
        Args:
            metadata: Metadata dictionary
            file_path: Storage file path
        """
        full_path = self.base_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(full_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=4, ensure_ascii=False)
        except Exception as e:
            raise StorageError(f"Failed to save metadata to {full_path}: {e}")
    
    def load_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Load metadata from JSON file.
        
        Args:
            file_path: Storage file path
            
        Returns:
            Metadata dictionary
        """
        full_path = self.base_path / file_path
        
        if not full_path.exists():
            raise StorageError(f"File not found: {full_path}")
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise StorageError(f"Failed to load metadata from {full_path}: {e}")
    
    def exists(self, file_path: str) -> bool:
        """
        Check if file exists in storage.
        
        Args:
            file_path: Storage file path
            
        Returns:
            True if file exists, False otherwise
        """
        full_path = self.base_path / file_path
        return full_path.exists()
