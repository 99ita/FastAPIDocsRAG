#!/usr/bin/env python3
"""
FastAPI Documentation RAG Embedding Generation Script

This script generates embeddings for processed document chunks using Vertex AI.
"""

import sys
import os
import json
import time
from pathlib import Path
from typing import List, Dict, Any

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

try:
    from dotenv import load_dotenv
    import vertexai
    from vertexai.language_models import TextEmbeddingModel
    from google.oauth2 import service_account
except ImportError as e:
    print(f"Missing required dependency: {e}")
    print("Please install: pip install google-cloud-aiplatform python-dotenv google-auth")
    sys.exit(1)


def load_chunks(chunks_file: str) -> List[Dict[str, Any]]:
    """Load processed chunks from JSONL file."""
    chunks = []
    try:
        with open(chunks_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    chunk_data = json.loads(line)
                    chunks.append(chunk_data)
    except FileNotFoundError:
        print(f"Error: Chunks file not found: {chunks_file}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in chunks file: {e}")
        sys.exit(1)
    
    return chunks


def generate_embeddings_batch(model: TextEmbeddingModel, texts: List[str]) -> List[List[float]]:
    """Generate embeddings for a batch of texts."""
    try:
        embeddings = model.get_embeddings(texts)
        return [embedding.values for embedding in embeddings]
    except Exception as e:
        print(f"Error generating embeddings for batch: {e}")
        return []


def main():
    """Main embedding generation function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='FastAPI Documentation RAG Embedding Generation')
    parser.add_argument('--chunks', default='output/ingestion/processed_chunks.jsonl',
                       help='Path to processed chunks file')
    parser.add_argument('--output', default='output/embedding/vector_index_upload.jsonl',
                       help='Path to output embeddings file')
    parser.add_argument('--batch-size', type=int, default=10,
                       help='Batch size for embedding generation')
    parser.add_argument('--model', default='text-embedding-004',
                       help='Vertex AI embedding model')
    parser.add_argument('--delay', type=float, default=0.2,
                       help='Delay between batches in seconds')
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Get configuration from environment
    project_id = os.getenv('GCP_PROJECT_ID')
    location = os.getenv('GCP_LOCATION')
    credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    
    # Validate environment variables
    if not project_id or project_id == 'your-project-id':
        print("Error: Please set GCP_PROJECT_ID in .env file")
        sys.exit(1)
    
    if not location:
        print("Error: Please set GCP_LOCATION in .env file")
        sys.exit(1)
    
    if not credentials_path or not Path(credentials_path).exists():
        print(f"Error: Please set GOOGLE_APPLICATION_CREDENTIALS to valid path in .env file")
        sys.exit(1)
    
    try:
        # Initialize Vertex AI with service account
        print(f"Initializing Vertex AI...")
        print(f"Project: {project_id}")
        print(f"Location: {location}")
        print(f"Credentials: {credentials_path}")
        
        # Load service account credentials
        credentials = service_account.Credentials.from_service_account_file(credentials_path)
        vertexai.init(project=project_id, location=location, credentials=credentials)
        
        # Load embedding model
        print(f"Loading embedding model: {args.model}")
        model = TextEmbeddingModel.from_pretrained(args.model)
        
        # Load chunks
        print(f"Loading chunks from: {args.chunks}")
        chunks = load_chunks(args.chunks)
        print(f"Loaded {len(chunks)} chunks")
        
        if not chunks:
            print("No chunks found to process")
            return
        
        # Create output directory
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Process chunks in batches
        total_chunks = len(chunks)
        batch_size = args.batch_size
        embeddings_data = []
        
        print(f"Processing {total_chunks} chunks in batches of {batch_size}...")
        
        for i in range(0, total_chunks, batch_size):
            batch_end = min(i + batch_size, total_chunks)
            batch_chunks = chunks[i:batch_end]
            
            # Extract text content from chunks
            texts = [chunk['page_content'] for chunk in batch_chunks]
            
            # Generate embeddings
            embeddings = generate_embeddings_batch(model, texts)
            
            # Prepare output data
            for j, (chunk, embedding) in enumerate(zip(batch_chunks, embeddings)):
                chunk_id = chunk['metadata']['id']
                embeddings_data.append({
                    'id': chunk_id,
                    'embedding': embedding
                })
            
            # Progress update
            processed_count = batch_end
            progress = (processed_count / total_chunks) * 100
            print(f"Batch {i//batch_size + 1} complete. {processed_count}/{total_chunks} chunks embedded ({progress:.1f})...")
            
            # Rate limiting delay
            if i + batch_size < total_chunks:  # Don't sleep after the last batch
                time.sleep(args.delay)
        
        # Save embeddings
        print(f"Saving embeddings to: {args.output}")
        with open(output_path, 'w', encoding='utf-8') as f:
            for data in embeddings_data:
                f.write(json.dumps(data) + '\n')
        
        print(f"Embedding generation completed!")
        print(f"Generated {len(embeddings_data)} embeddings")
        print(f"Output saved to: {args.output}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
