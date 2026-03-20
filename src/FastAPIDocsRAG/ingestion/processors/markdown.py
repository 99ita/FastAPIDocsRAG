"""
Markdown-specific processing utilities.
"""

import os
from typing import List
from pathlib import Path


class MarkdownProcessor:
    """Utilities for processing markdown files."""
    
    @staticmethod
    def load_markdown_files(docs_dir: str) -> List[tuple]:
        """
        Load all markdown files from a directory.
        
        Args:
            docs_dir: Directory containing markdown files
            
        Returns:
            List of (content, source_path) tuples
        """
        markdown_files = []
        docs_path = Path(docs_dir)
        
        if not docs_path.exists():
            raise FileNotFoundError(f"Documentation directory not found: {docs_dir}")
        
        for file_path in docs_path.rglob("*.md"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                markdown_files.append((content, str(file_path)))
            except Exception as e:
                print(f"Warning: Failed to read {file_path}: {e}")
        
        return markdown_files
