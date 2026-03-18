"""
Document processing components.
"""

import re
from typing import List, Dict, Any, Tuple
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_core.documents import Document

from ..cleaners.markdown import DataCleaner
from ...core.exceptions import ProcessingError


class DocumentProcessor:
    """Process documents by splitting and enriching them with context."""
    
    def __init__(self, docs_src_path: str = "./docs_src"):
        """
        Initialize document processor.
        
        Args:
            docs_src_path: Path to source code directory for code extraction
        """
        # FastAPI uses {#id} in headers, let's clean this for better context
        self.anchor_pattern = re.compile(r'\{ #.*? \}')
        
        self.headers_to_split_on = [
            ("#", "H1"),
            ("##", "H2"),
            ("###", "H3"),
        ]
        self.splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=self.headers_to_split_on,
            strip_headers=False 
        )
        
        # Stateful header tracking
        self.current_h1 = ""
        self.current_h2 = ""
        self.current_h3 = ""
        
        # Initialize cleaner
        self.cleaner = DataCleaner(docs_src_path)
    
    def _clean_header(self, header_text: str) -> str:
        """Remove anchor IDs like {#concurrency-and-async-await}"""
        return self.anchor_pattern.sub('', header_text).strip()
    
    def _update_header_state(self, chunk_metadata: dict):
        """Update persistent header state based on current chunk metadata"""
        # Always update if header metadata exists, not only when different
        if "H1" in chunk_metadata and chunk_metadata["H1"]:
            new_h1 = self._clean_header(chunk_metadata["H1"])
            self.current_h1 = new_h1
            self.current_h2 = ""  # Reset lower levels
            self.current_h3 = ""
        
        if "H2" in chunk_metadata and chunk_metadata["H2"]:
            new_h2 = self._clean_header(chunk_metadata["H2"])
            self.current_h2 = new_h2
            self.current_h3 = ""  # Reset lower level
        
        if "H3" in chunk_metadata and chunk_metadata["H3"]:
            new_h3 = self._clean_header(chunk_metadata["H3"])
            self.current_h3 = new_h3
    
    def _build_breadcrumb(self) -> str:
        """Build breadcrumb from current header state"""
        levels = [level for level in [self.current_h1, self.current_h2, self.current_h3] if level]
        return " > ".join(levels)
    
    def process_document(self, doc_content: str, source_name: str) -> Tuple[List[Document], Dict[str, int]]:
        """
        Process a document by splitting and enriching it.
        
        Args:
            doc_content: Raw document content
            source_name: Source file name
            
        Returns:
            Tuple of (processed_chunks, code_statistics)
        """
        try:
            # Reset state for new document
            self.current_h1 = ""
            self.current_h2 = ""
            self.current_h3 = ""
            
            # Count code references in original document
            total_references = len(re.findall(r'\{\*\s*[^}]+?\s+hl\[[^\]]+\]\s*\*\}', doc_content))
            
            # 1. Initial split by headers
            chunks = self.splitter.split_text(doc_content)
            
            enriched_chunks = []
            successful_extractions = 0
            failed_extractions = 0
            
            for chunk in chunks:
                # Count references in this chunk
                chunk_references = len(re.findall(r'\{\*\s*[^}]+?\s+hl\[[^\]]+\]\s*\*\}', chunk.page_content))
                
                # 2. Update persistent header state
                self._update_header_state(chunk.metadata)
                
                # 3. Build breadcrumb from current state
                breadcrumb = self._build_breadcrumb()
                
                # 4. Clean and enhance content
                cleaned_content = self.cleaner.clean_markdown(chunk.page_content)
                
                # Check if extraction was successful
                if chunk_references > 0 and cleaned_content != chunk.page_content:
                    successful_extractions += chunk_references
                elif chunk_references > 0:
                    failed_extractions += chunk_references
                
                # 5. Context Injection
                enriched_content = f"[Context: {breadcrumb}]\n\n{cleaned_content}"
                
                # 6. Create enriched Document with clean metadata
                enriched_chunks.append(Document(
                    page_content=enriched_content,
                    metadata={
                        "source": source_name,
                        "hierarchy": [level for level in [self.current_h1, self.current_h2, self.current_h3] if level],
                        "breadcrumb": breadcrumb
                    }
                ))
            
            code_stats = {
                "total_references": total_references,
                "successful_extractions": successful_extractions,
                "failed_extractions": failed_extractions
            }
            
            return enriched_chunks, code_stats
            
        except Exception as e:
            raise ProcessingError(f"Failed to process document {source_name}: {e}")
