"""
Main RAG pipeline orchestration.
"""

import os
import re
from typing import List, Dict, Any, Tuple
from pathlib import Path

from langchain_core.documents import Document

from .config import Config
from .exceptions import PipelineError, ProcessingError, StorageError
from ..ingestion.processors.document import DocumentProcessor
from ..ingestion.processors.markdown import MarkdownProcessor
from ..ingestion.extractors.metadata import get_mkdocs_parser
from ..ingestion.cleaners.markdown import DataCleaner
from ..storage.local import LocalStorage


class RAGPipeline:
    """Main pipeline for document ingestion and processing."""
    
    def __init__(self, config: Config):
        """
        Initialize the RAG pipeline.
        
        Args:
            config: Configuration object
        """
        self.config = config
        
        # Initialize components
        self.document_processor = DocumentProcessor(self.config.docs_src_dir)
        self.markdown_processor = MarkdownProcessor()
        self.data_cleaner = DataCleaner(self.config.docs_src_dir)
        self.mkdocs_parser = get_mkdocs_parser(self.config.mkdocs_config)
        
        # Initialize storage
        if self.config.storage_type == "local":
            self.storage = LocalStorage()
        else:
            raise PipelineError(f"Unsupported storage type: {self.config.storage_type}")
    
    def run_ingestion(self) -> Dict[str, Any]:
        """
        Run the complete ingestion pipeline.
        
        Returns:
            Dictionary with pipeline statistics
        """
        try:
            # A. Load documents
            raw_docs = self._load_documents()
            print(f"Loaded {len(raw_docs)} documents from {self.config.docs_dir}")
            
            # B. Process documents
            all_chunks, code_stats = self._process_documents(raw_docs)
            print(f"Generated {len(all_chunks)} chunks")
            print(f"Code references: {code_stats['successful_extractions']}/{code_stats['total_references']} extracted")
            
            # C. Enhanced content cleaning and optimization
            optimized_chunks, _ = self._enhance_chunks(all_chunks)
            print(f"Optimized to {len(optimized_chunks)} chunks")
            
            # D. Quality control and filtering
            filtered_chunks, filtered_out_chunks, quality_stats = self._filter_chunks(optimized_chunks)
            print(f"Quality control: {quality_stats['filtered_out']} chunks filtered out")
            print(f"Final chunk count: {quality_stats['final_chunks']}")
            
            # E. MkDocs metadata enhancement
            enhanced_chunks, mkdocs_stats = self._enhance_with_metadata(filtered_chunks)
            print(f"MkDocs Enhancement: {mkdocs_stats['enhanced_with_mkdocs']}/{mkdocs_stats['total_chunks']} chunks enhanced")
            print(f"Sections found: {', '.join(mkdocs_stats['sections_found'])}")
            
            # F. Save results
            self._save_results(enhanced_chunks)
            
            # G. Save filtered out chunks for analysis
            self._save_filtered_chunks(filtered_out_chunks)
            
            # H. Create lookup table
            self._create_lookup_table(enhanced_chunks)
            
            return {
                'total_documents': len(raw_docs),
                'total_chunks': len(enhanced_chunks),
                'code_stats': code_stats,
                'quality_stats': quality_stats,
                'mkdocs_stats': mkdocs_stats
            }
            
        except Exception as e:
            raise PipelineError(f"Pipeline execution failed: {e}")
    
    def _load_documents(self) -> List[tuple]:
        """Load documents from the configured directory."""
        try:
            return self.markdown_processor.load_markdown_files(self.config.docs_dir)
        except Exception as e:
            raise ProcessingError(f"Failed to load documents: {e}")
    
    def _process_documents(self, raw_docs: List[tuple]) -> Tuple[List[Document], Dict[str, Any]]:
        """Process documents into chunks."""
        all_chunks = []
        code_stats = {
            "total_references": 0,
            "successful_extractions": 0,
            "failed_extractions": 0
        }
        
        for content, source_path in raw_docs:
            try:
                chunks, doc_code_stats = self.document_processor.process_document(content, source_path)
                all_chunks.extend(chunks)
                
                # Aggregate code statistics
                code_stats["total_references"] += doc_code_stats["total_references"]
                code_stats["successful_extractions"] += doc_code_stats["successful_extractions"]
                code_stats["failed_extractions"] += doc_code_stats["failed_extractions"]
                
            except Exception as e:
                print(f"Warning: Failed to process {source_path}: {e}")
        
        return all_chunks, code_stats
    
    def _enhance_chunks(self, chunks: List[Document]) -> tuple[List[Document], Dict[str, Any]]:
        """Enhance chunks with cleaning and optimization."""
        optimized_chunks = []
        code_stats = {
            "total_references": 0,
            "successful_extractions": 0,
            "failed_extractions": 0
        }
        
        for chunk in chunks:
            # Count code references in original content BEFORE cleaning
            references_in_chunk = len(re.findall(r'\{\*\s*[^}]+?\s+hl\[[^\]]+\]\s*\*\}', chunk.page_content))
            code_stats["total_references"] += references_in_chunk
            
            # Clean content with enhanced cleaner
            cleaned_content = self.data_cleaner.clean_markdown(chunk.page_content)
            
            # Check if extraction was successful
            if references_in_chunk > 0 and cleaned_content != chunk.page_content:
                code_stats["successful_extractions"] += references_in_chunk
            elif references_in_chunk > 0:
                code_stats["failed_extractions"] += references_in_chunk
            
            # Optimize chunk length
            optimized_content_pieces = self.data_cleaner.optimize_chunk_length(cleaned_content)
            
            for content_piece in optimized_content_pieces:
                # Extract keywords for better retrieval
                keywords = self.data_cleaner.extract_keywords(content_piece)
                
                # Assess content quality
                quality_metrics = self.data_cleaner.assess_content_quality(content_piece)
                
                # Create enhanced chunk
                chunk_id = f"fastapi_{len(optimized_chunks)}"
                enhanced_chunk = Document(
                    page_content=chunk.page_content,
                    metadata={
                        **chunk.metadata,
                        'id': chunk_id,
                        'keywords': keywords,
                        'quality_metrics': quality_metrics
                    }
                )
                optimized_chunks.append(enhanced_chunk)
        
        return optimized_chunks, code_stats
    
    def _filter_chunks(self, chunks: List[Document]) -> tuple[List[Document], List[Document], Dict[str, Any]]:
        """Filter chunks based on quality criteria."""
        filtered_chunks = []
        filtered_out_chunks = []
        quality_stats = {
            'total_chunks': len(chunks),
            'filtered_out': 0,
            'avg_word_count': 0
        }
        
        min_word_count = self.config.get("ingestion.quality_filters.min_word_count", 10)
        max_word_count = self.config.get("ingestion.quality_filters.max_word_count", 2000)
        
        # Debug output to verify configuration values
        print(f"DEBUG: Using min_word_count: {min_word_count}")
        print(f"DEBUG: Using max_word_count: {max_word_count}")
        
        for chunk in chunks:
            quality = chunk.metadata.get('quality_metrics', {})
            
            # Filter out low-quality chunks
            word_count = quality.get('word_count', 0)
            
            # Keep chunks with meaningful content (only word count filtering)
            if (word_count >= min_word_count and
                word_count <= max_word_count):
                filtered_chunks.append(chunk)
            else:
                filtered_out_chunks.append(chunk)
                quality_stats['filtered_out'] += 1
        
        # Calculate quality statistics
        if filtered_chunks:
            total_words = sum(chunk.metadata.get('quality_metrics', {}).get('word_count', 0) for chunk in filtered_chunks)
            
            quality_stats['avg_word_count'] = total_words / len(filtered_chunks)
        
        quality_stats['final_chunks'] = len(filtered_chunks)
        
        return filtered_chunks, filtered_out_chunks, quality_stats
    
    def _enhance_with_metadata(self, chunks: List[Document]) -> tuple[List[Document], Dict[str, Any]]:
        """Enhance chunks with MkDocs metadata."""
        enhanced_chunks = []
        mkdocs_stats = {
            "total_chunks": len(chunks),
            "enhanced_with_mkdocs": 0,
            "sections_found": set()
        }
        
        for chunk in chunks:
            source_path = chunk.metadata.get("source", "")
            
            # Get MkDocs metadata for this file
            mkdocs_metadata = self.mkdocs_parser.get_metadata_for_file(source_path)
            
            # Merge MkDocs metadata with existing metadata
            enhanced_metadata = {
                **chunk.metadata,
                **mkdocs_metadata
            }
            
            # Track statistics
            if mkdocs_metadata.get("section"):
                mkdocs_stats["enhanced_with_mkdocs"] += 1
                mkdocs_stats["sections_found"].add(mkdocs_metadata["section"])
            
            # Create enhanced chunk
            enhanced_chunk = Document(
                page_content=chunk.page_content,
                metadata=enhanced_metadata
            )
            enhanced_chunks.append(enhanced_chunk)
        
        mkdocs_stats["sections_found"] = list(mkdocs_stats["sections_found"])
        
        return enhanced_chunks, mkdocs_stats
    
    def _save_results(self, chunks: List[Document]):
        """Save processed chunks to storage."""
        try:
            chunks_file = self.config.get("storage.local.chunks_file", "processed_chunks.jsonl")
            self.storage.save_chunks(chunks, chunks_file)
            print(f"Saved {len(chunks)} chunks to {chunks_file}")
        except Exception as e:
            raise StorageError(f"Failed to save chunks: {e}")
    
    def _create_lookup_table(self, chunks: List[Document]):
        """Create enhanced lookup table for metadata."""
        try:
            lookup_table = {}
            for chunk in chunks:
                chunk_id = chunk.metadata.get("id", f"fastapi_{len(lookup_table)}")
                lookup_table[chunk_id] = {
                    "id": chunk_id,
                    "text": chunk.page_content,
                    "source": chunk.metadata.get("source"),
                    "keywords": chunk.metadata.get("keywords", []),
                    "hierarchy": chunk.metadata.get("hierarchy", []),
                    "breadcrumb": chunk.metadata.get("breadcrumb", ""),
                    "quality_metrics": chunk.metadata.get("quality_metrics", {}),
                    # MkDocs enhanced metadata
                    "navigation_title": chunk.metadata.get("navigation_title", ""),
                    "navigation_path": chunk.metadata.get("navigation_path", ""),
                    "section": chunk.metadata.get("section", ""),
                    "learning_level": chunk.metadata.get("learning_level", ""),
                    "difficulty": chunk.metadata.get("difficulty", "")
                }
            
            metadata_file = self.config.get("storage.local.metadata_file", "metadata_lookup.json")
            self.storage.save_metadata(lookup_table, metadata_file)
            print(f"Created lookup table with {len(lookup_table)} entries")
            
        except Exception as e:
            raise StorageError(f"Failed to create lookup table: {e}")
    
    def _save_filtered_chunks(self, chunks: List[Document]):
        """Save filtered out chunks for analysis."""
        try:
            filtered_file = self.config.get("storage.local.filtered_chunks_file", "filtered_chunks.jsonl")
            self.storage.save_chunks(chunks, filtered_file)
            print(f"Saved {len(chunks)} filtered chunks to {filtered_file}")
        except Exception as e:
            raise StorageError(f"Failed to save filtered chunks: {e}")
