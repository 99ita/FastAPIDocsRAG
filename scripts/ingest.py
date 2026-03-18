#!/usr/bin/env python3
"""
FastAPI Documentation RAG Ingestion Script

This script runs the document ingestion pipeline to process FastAPI documentation
and create enhanced chunks with metadata for RAG applications.
"""

import sys
import os
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from FastAPIDocsRAG.core.config import Config
from FastAPIDocsRAG.core.pipeline import RAGPipeline


def main():
    """Main ingestion function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='FastAPI Documentation RAG Ingestion')
    parser.add_argument('--config', default='config', 
                       help='Path to configuration directory')
    parser.add_argument('--environment', default='development',
                       help='Environment (development, production, test)')
    
    args = parser.parse_args()
    
    try:
        # Initialize configuration
        config = Config(config_path=args.config, environment=args.environment)
        
        print(f"Starting FastAPI Documentation RAG ingestion...")
        print(f"Configuration: {args.environment}")
        print(f"Docs directory: {config.docs_dir}")
        print(f"Docs source directory: {config.docs_src_dir}")
        print(f"MkDocs config: {config.mkdocs_config}")
        print("-" * 50)
        
        # Initialize and run pipeline
        pipeline = RAGPipeline(config)
        stats = pipeline.run_ingestion()
        
        print("-" * 50)
        print("Ingestion completed successfully!")
        print(f"Documents processed: {stats['total_documents']}")
        print(f"Chunks generated: {stats['total_chunks']}")
        
        if stats['code_stats']['total_references'] > 0:
            success_rate = (stats['code_stats']['successful_extractions'] / stats['code_stats']['total_references']) * 100
            print(f"Code reference extraction: {success_rate:.1f}% success rate")
        
        print(f"Average word count: {stats['quality_stats']['avg_word_count']:.1f}")
        
        if stats['mkdocs_stats']['sections_found']:
            print(f"Sections enhanced: {', '.join(stats['mkdocs_stats']['sections_found'])}")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
