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
    
    @staticmethod
    def extract_frontmatter(content: str) -> tuple:
        """
        Extract frontmatter from markdown content.
        
        Args:
            content: Raw markdown content
            
        Returns:
            Tuple of (frontmatter_dict, content_without_frontmatter)
        """
        import re
        
        frontmatter_pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
        match = re.match(frontmatter_pattern, content, re.DOTALL)
        
        if match:
            try:
                import yaml
                frontmatter = yaml.safe_load(match.group(1)) or {}
                content = match.group(2)
                return frontmatter, content
            except yaml.YAMLError:
                pass
        
        return {}, content
