#!/usr/bin/env python3
"""
FastAPI Documentation RAG Query Script

This script provides a command-line interface for querying the RAG system.
"""

import sys
import os
import json
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

try:
    from dotenv import load_dotenv
    from FastAPIDocsRAG.core.config import Config
    from FastAPIDocsRAG.query.rag_engine import RAGEngine
except ImportError as e:
    print(f"Missing required dependency: {e}")
    print("Please install: pip install python-dotenv")
    sys.exit(1)


def main():
    """Main query function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='FastAPI Documentation RAG Query System')
    parser.add_argument('query', help='Question to ask about FastAPI')
    parser.add_argument('--top-n', type=int, default=5,
                       help='Number of documents to retrieve (default: 5)')
    parser.add_argument('--environment', default='development',
                       choices=['development', 'production'],
                       help='Environment configuration to use')
    parser.add_argument('--config', type=str,
                       help='Path to configuration directory')
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Initialize configuration
    config = Config(config_path=args.config, environment=args.environment)
    
    # Initialize RAG engine
    metadata_file = Path(config.ingestion_output_dir) / "metadata_lookup.json"
    rag_engine = RAGEngine(config, str(metadata_file))
    
    print(f"FastAPI Documentation RAG Query System")
    print(f"Environment: {args.environment}")
    print(f"Query: {args.query}")
    print(f"Retrieving top {args.top_n} documents...")
    
    # Generate answer
    result = rag_engine.generate_answer(args.query, top_n=args.top_n)
    
    # Display results
    print("\n" + "="*60)
    print("ANSWER:")
    print("="*60)
    print(result['answer'])
    
    if result.get('sources'):
        print("\n" + "="*60)
        print("SOURCES:")
        print("="*60)
        for i, source in enumerate(result['sources'], 1):
            print(f"{i}. {source}")
    
    print("\n" + "="*60)
    print("METADATA:")
    print("="*60)
    print(f"Documents retrieved: {result.get('documents_retrieved', 'N/A')}")
    print(f"Context length: {result.get('context_length', 'N/A')} characters")
    print(f"Model used: {result.get('model', 'N/A')}")
    print(f"Tokens used: {result.get('tokens_used', 'N/A')}")
    
    if result.get('error'):
        print(f"\nError: {result['error']}")


if __name__ == "__main__":
    main()
