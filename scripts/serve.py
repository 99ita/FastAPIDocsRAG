#!/usr/bin/env python3
"""
FastAPI Documentation RAG API Server

This script starts the FastAPI server for the RAG system.
"""

import sys
import os
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

try:
    from FastAPIDocsRAG.api.rag_api import RAGAPI
except ImportError as e:
    print(f"Missing required dependency: {e}")
    print("Please install: pip install fastapi uvicorn python-dotenv")
    sys.exit(1)

def main():
    """Main server function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='FastAPI Documentation RAG API Server')
    parser.add_argument('--host', default='0.0.0.0',
                       help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8000,
                       help='Port to bind to (default: 8000)')
    parser.add_argument('--environment', default='development',
                       choices=['development', 'production'],
                       help='Environment configuration to use')
    parser.add_argument('--config', type=str,
                       help='Path to configuration directory')
    parser.add_argument('--reload', action='store_true',
                       help='Enable auto-reload for development')
    
    args = parser.parse_args()
    
    # Initialize RAG API
    rag_api = RAGAPI(config_path=args.config, environment=args.environment)
    
    print("FastAPI Documentation RAG API Server")
    print(f"Environment: {args.environment}")
    print(f"Configuration: {args.config or 'default'}")
    print(f"Server: http://{args.host}:{args.port}")
    print(f"Auto-reload: {args.reload}")
    
    # Run the server
    rag_api.run(host=args.host, port=args.port)

if __name__ == "__main__":
    main()
