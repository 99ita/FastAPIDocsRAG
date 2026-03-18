"""
Markdown cleaning and content enhancement utilities.
"""

import re
import textwrap
from typing import List, Dict, Any

from ..extractors.code import get_code_extractor


class DataCleaner:
    """Enhanced markdown cleaning with semantic preservation and code reference extraction."""
    
    def __init__(self, docs_src_path: str = "./docs_src"):
        """
        Initialize data cleaner.
        
        Args:
            docs_src_path: Path to source code directory for code extraction
        """
        self.code_extractor = get_code_extractor(docs_src_path)
    
    @staticmethod
    def clean_markdown(text: str, docs_src_path: str = "./docs_src") -> str:
        """Enhanced markdown cleaning with semantic preservation and code reference extraction."""
        # 1. Process code references first (before other code processing)
        text = DataCleaner._process_code_references(text, docs_src_path)
        
        # 2. Extract and preserve code blocks
        text = DataCleaner._process_code_blocks(text)
        
        # 3. Clean markdown links to text references
        text = DataCleaner._normalize_links(text)
        
        # 4. Handle emphasis and formatting (preserve semantic meaning)
        text = DataCleaner._process_formatting(text)
        
        # 5. Clean lists and normalize structure
        text = DataCleaner._normalize_lists(text)
        
        # 6. Remove HTML tags (like <abbr>, <strong>)
        text = re.sub(r'<[^>]*>', '', text)
        
        # 7. Clean FastAPI anchor IDs (ex: { #concurrency })
        text = re.sub(r'\{ #.*? \}', '', text)
        
        # 8. Remove emojis and special Unicode characters
        text = DataCleaner._remove_emojis(text)
        
        # 9. Normalize whitespace and line breaks
        text = DataCleaner._normalize_whitespace(text)
        
        return text
    
    @staticmethod
    def _process_code_references(text: str, docs_src_path: str) -> str:
        """Process code references and extract actual code."""
        code_extractor = get_code_extractor(docs_src_path)
        return code_extractor.process_code_references(text)
    
    @staticmethod
    def _process_code_blocks(text: str) -> str:
        """Extract code blocks and replace with clean markers, but preserve extracted code references."""
        # Handle code blocks first - use a simpler approach
        code_blocks = []
        
        def replace_code_block(match):
            code = match.group(0)
            
            # Check if this is an extracted code reference (contains python code from our extractor)
            if '```python\n' in code and 'extracted_lines' not in code:
                # This might be an extracted reference, let's check if it contains actual code
                content = re.sub(r'```python\n?(.*?)\n?```', r'\1', code, flags=re.DOTALL)
                # If it looks like real code (has imports, functions, etc.), preserve it
                if any(keyword in content for keyword in ['import ', 'def ', 'class ', '@', 'from ']):
                    return code  # Preserve the extracted code block
            
            clean_code = re.sub(r'\s+', ' ', code.strip())
            # Extract just the code content between the backticks
            content = re.sub(r'```[\w]*\n?(.*?)\n?```', r'\1', code, flags=re.DOTALL)
            clean_content = re.sub(r'\s+', ' ', content.strip())[:50]
            marker = f"[CODE_BLOCK_{len(code_blocks)}: {clean_content}...]"
            code_blocks.append(marker)
            return marker
        
        # Replace code blocks
        text = re.sub(r'```[\w]*\n.*?\n```', replace_code_block, text, flags=re.DOTALL)
        
        # Handle inline code
        def replace_inline(match):
            code = match.group(1)
            if not code.startswith('CODE_BLOCK_') and len(code) < 100:
                return f"[CODE: {code}]"
            return match.group(0)
        
        text = re.sub(r'`([^`\n]+)`', replace_inline, text)
        
        return text
    
    @staticmethod
    def _normalize_links(text: str) -> str:
        """Convert markdown links to text references."""
        # Convert [text](url) to just text
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        # Convert reference-style links [text][ref] to just text
        text = re.sub(r'\[([^\]]+)\]\[[^\]]*\]', r'\1', text)
        return text
    
    @staticmethod
    def _process_formatting(text: str) -> str:
        """Handle emphasis and formatting while preserving semantic meaning."""
        # Convert bold **text** to [BOLD:text] for semantic preservation
        text = re.sub(r'\*\*([^*]+)\*\*', r'[BOLD:\1]', text)
        # Convert italic *text* to [ITALIC:text]
        text = re.sub(r'\*([^*]+)\*', r'[ITALIC:\1]', text)
        # Convert __text__ to [BOLD:text]
        text = re.sub(r'__([^_]+)__', r'[BOLD:\1]', text)
        # Convert _text_ to [ITALIC:text]
        text = re.sub(r'_([^_]+)_', r'[ITALIC:\1]', text)
        return text
    
    @staticmethod
    def _normalize_lists(text: str) -> str:
        """Normalize list structures."""
        # Normalize ordered lists
        text = re.sub(r'^\s*\d+\.\s+', '- ', text, flags=re.MULTILINE)
        # Normalize unordered lists
        text = re.sub(r'^\s*[-*+]\s+', '- ', text, flags=re.MULTILINE)
        return text
    
    @staticmethod
    def _remove_emojis(text: str) -> str:
        """Remove emojis and special Unicode characters."""
        # Remove emojis (basic pattern)
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+", flags=re.UNICODE
        )
        return emoji_pattern.sub('', text)
    
    @staticmethod
    def _normalize_whitespace(text: str) -> str:
        """Normalize whitespace and line breaks."""
        # Normalize line breaks
        text = re.sub(r'\r\n', '\n', text)
        # Remove excessive blank lines
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Normalize spaces
        text = re.sub(r' +', ' ', text)
        # Remove leading/trailing whitespace from lines
        lines = [line.strip() for line in text.split('\n')]
        return '\n'.join(lines)
    
    @staticmethod
    def optimize_chunk_length(text: str, max_length: int = 1000) -> List[str]:
        """Split text into optimally sized chunks."""
        if len(text) <= max_length:
            return [text]
        
        chunks = []
        sentences = re.split(r'(?<=[.!?])\s+', text)
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= max_length:
                current_chunk += sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    @staticmethod
    def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
        """Extract keywords from text."""
        # Simple keyword extraction - look for technical terms
        technical_terms = [
            'fastapi', 'api', 'endpoint', 'request', 'response', 'model',
            'pydantic', 'validation', 'authentication', 'authorization',
            'dependency', 'injection', 'middleware', 'cors', 'websocket',
            'async', 'await', 'uvicorn', 'python', 'http', 'json',
            'schema', 'query', 'path', 'parameter', 'header', 'cookie'
        ]
        
        text_lower = text.lower()
        keywords = []
        
        for term in technical_terms:
            if term in text_lower and term not in keywords:
                keywords.append(term)
                if len(keywords) >= max_keywords:
                    break
        
        return keywords
    
    @staticmethod
    def assess_content_quality(text: str) -> Dict[str, Any]:
        """Assess the quality of content."""
        word_count = len(text.split())
        char_count = len(text)
        
        # Code density (ratio of code markers)
        code_markers = ['[CODE:', '[CODE_BLOCK_', '[BOLD:', '[ITALIC:']
        code_count = sum(1 for marker in code_markers if marker in text)
        code_density = code_count / max(word_count, 1)
        
        return {
            'word_count': word_count,
            'char_count': char_count,
            'code_density': code_density,
            'quality_score': min(1.0, (word_count / 100) + code_density)
        }
