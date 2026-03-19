"""
RAG Engine that combines Vector Search and Gemini for document Q&A.
"""

import json
import os
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

from .vector_search import VectorSearchClient
from .gemini_client import GeminiClient


class RAGEngine:
    """Retrieval-Augmented Generation engine for FastAPI documentation."""
    
    def __init__(self, config, metadata_file: str = None):
        """
        Initialize RAG engine.
        
        Args:
            config: Configuration object
            metadata_file: Path to metadata lookup file
        """
        self.config = config
        self.metadata_lookup = {}
        self._vertexai_initialized = False
        
        # Load metadata lookup
        if metadata_file:
            self._load_metadata(metadata_file)
        
        # Initialize clients (will be created when needed)
        self.vector_client = None
        self.gemini_client = None
        
        # Initialize logging configuration
        self.logging_enabled = config.get("logging.enabled", True)
        self.log_dir = config.get("logging.log_dir", "./output/logs")
    
    def _initialize_vertexai(self):
        """Initialize Vertex AI once for all components."""
        if not self._vertexai_initialized:
            from dotenv import load_dotenv
            import vertexai
            from google.oauth2 import service_account
            
            project_id = os.getenv('GCP_PROJECT_ID')
            location = os.getenv('GCP_LOCATION')
            credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
            
            if not all([project_id, location, credentials_path]):
                raise ValueError("Missing GCP configuration. Please check .env file.")
            
            # Initialize Vertex AI once
            credentials = service_account.Credentials.from_service_account_file(credentials_path)
            vertexai.init(project=project_id, location=location, credentials=credentials)
            self._vertexai_initialized = True
    
    def _get_vector_client(self):
        """Get or create vector search client."""
        if not self.vector_client:
            from .vector_search import VectorSearchClient
            self.vector_client = VectorSearchClient(self.config)
        return self.vector_client
    
    def _get_gemini_client(self):
        """Get or create Gemini client."""
        if not self.gemini_client:
            from .gemini_client import GeminiClient
            self.gemini_client = GeminiClient(self.config)
        return self.gemini_client
    
    def _load_metadata(self, metadata_file: str):
        """
        Load metadata lookup file into global dictionary.
        
        Args:
            metadata_file: Path to metadata JSON file
        """
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                self.metadata_lookup = json.load(f)
            print(f"Loaded {len(self.metadata_lookup)} metadata entries")
        except FileNotFoundError:
            print(f"Warning: Metadata file not found: {metadata_file}")
            self.metadata_lookup = {}
        except json.JSONDecodeError as e:
            print(f"Error loading metadata: {e}")
            self.metadata_lookup = {}
    
    def get_relevant_context(self, query_text: str, top_n: int = 5, logger=None) -> Dict[str, Any]:
        """
        Retrieve relevant context for a query.
        
        Args:
            query_text: User's search query
            top_n: Number of documents to retrieve
            logger: Optional QueryLogger instance
            
        Returns:
            Dictionary with context string and similar documents
        """
        try:
            if logger:
                logger.log_vector_search_start(query_text)
            
            # Convert query to embedding
            vector_client = self._get_vector_client()
            
            if logger:
                with logger.timer("EMBEDDING", "Query embedding generation"):
                    query_embedding = vector_client.query_to_embedding(query_text, logger=logger)
            else:
                query_embedding = vector_client.query_to_embedding(query_text)
            
            # Find similar documents
            if logger:
                with logger.timer("VECTOR_SEARCH", "Document similarity search"):
                    similar_docs = vector_client.find_neighbors(query_embedding, top_k=top_n, logger=logger)
            else:
                similar_docs = vector_client.find_neighbors(query_embedding, top_k=top_n)
            
            if not similar_docs:
                if logger:
                    logger.log_warning("VECTOR_SEARCH", "No similar documents found")
                return {
                    "context": "No relevant documentation found.",
                    "similar_docs": []
                }
            
            # Format context with metadata
            context_parts = []
            sources = []
            
            doc_counter = 0
            for doc in similar_docs:
                doc_counter += 1
                doc_id = doc.get("id", "")
                metadata = self.metadata_lookup.get(doc_id, {})
                
                if metadata:
                    # Format document information
                    doc_info = {
                        "id": doc_id,
                        "content": metadata.get("text", "").replace("\\n", "\n"),  # Convert literal \n to actual line breaks
                        "source": metadata.get("source", ""),
                        "breadcrumb": metadata.get("breadcrumb", ""),
                        "navigation_path": metadata.get("navigation_path", ""),
                        "keywords": metadata.get("keywords", []),
                        "similarity": doc.get("similarity", 0.0)
                    }
                    
                    context_parts.append(f"Document {doc_counter}:")
                    context_parts.append(f"Source: {doc_info['source']}")
                    context_parts.append(f"Navigation: {doc_info['breadcrumb']}")
                    context_parts.append(f"Content: {doc_info['content'][:500]}...")
                    context_parts.append("")  # Empty line for readability
                    
                    if doc_info['source'] not in sources:
                        sources.append(doc_info['source'])
            
            # Combine all context parts
            context = "\n".join(context_parts)
            
            if logger:
                logger.log_context_assembly(len(context), sources)
            
            return {
                "context": context,
                "similar_docs": similar_docs
            }
            
        except Exception as e:
            error_msg = f"Error retrieving context: {e}"
            if logger:
                logger.log_error("CONTEXT_RETRIEVAL", e, {"query_text": query_text, "top_n": top_n})
            
            return {
                "context": f"Error retrieving context: {str(e)}",
                "similar_docs": []
            }
    
    def generate_answer(self, query_text: str, top_n: int = 5, logger=None) -> Dict[str, Any]:
        """
        Generate answer using RAG approach.
        
        Args:
            query_text: User's question
            top_n: Number of documents to retrieve
            logger: Optional QueryLogger instance
            
        Returns:
            Dictionary with answer, sources, and metadata
        """
        try:
            if logger:
                logger.log_info("RAG_ENGINE", "Starting answer generation", {
                    "query": query_text,
                    "top_n": top_n
                })
            
            # Get relevant context
            context_result = self.get_relevant_context(query_text, top_n, logger)
            context = context_result.get("context", "")
            similar_docs = context_result.get("similar_docs", [])
            
            # Check if no relevant context was found - skip Gemini call
            if (not similar_docs or 
                not context or 
                "No relevant documentation found" in context or
                "unavailable" in context.lower()):
                
                if logger:
                    logger.log_warning("RAG_ENGINE", "No relevant context found, skipping Gemini call", {
                        "query": query_text,
                        "similar_docs_count": len(similar_docs),
                        "context_length": len(context) if context else 0
                    })
                
                return {
                    "query": query_text,
                    "answer": "No relevant documentation found for your query. Please try rephrasing your question or check if the topic is covered in the FastAPI documentation.",
                    "similar_docs": [],
                    "documents_retrieved": 0,
                    "context_length": 0,
                    "model": "none",  # Use string instead of None for Pydantic validation
                    "tokens_used": 0
                }
            
            # Generate answer with Gemini
            gemini_client = self._get_gemini_client()
            
            if logger:
                with logger.timer("GEMINI_GENERATION", "Answer generation with Gemini"):
                    response = gemini_client.generate_answer(query_text, context, logger=logger)
            else:
                response = gemini_client.generate_answer(query_text, context)
            
            result = {
                "query": query_text,
                "answer": response.get("answer", ""),
                "similar_docs": similar_docs,
                "context_length": len(context),
                "documents_retrieved": top_n,
                "model": response.get("model", "unknown"),
                "tokens_used": response.get("tokens_used", 0)
            }
            
            if logger:
                logger.log_response_generation(len(result["answer"]), time.time())
            
            return result
            
        except Exception as e:
            error_msg = f"Error generating answer: {e}"
            if logger:
                logger.log_error("ANSWER_GENERATION", e, {"query_text": query_text, "top_n": top_n})
            
            return {
                "query": query_text,
                "answer": f"Sorry, I encountered an error: {str(e)}",
                "sources": [],
                "error": str(e)
            }
