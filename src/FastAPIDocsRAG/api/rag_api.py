"""
FastAPI application for RAG (Retrieval-Augmented Generation) queries.
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_path))

try:
    from fastapi import FastAPI, HTTPException, Query
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, Field
    from dotenv import load_dotenv
    from FastAPIDocsRAG.core.config import Config
    from FastAPIDocsRAG.core.logging_utils import create_query_logger
    from FastAPIDocsRAG.query.rag_engine import RAGEngine
except ImportError as e:
    print(f"Missing required dependency: {e}")
    print("Please install: pip install fastapi python-dotenv")
    raise ImportError(f"Missing dependencies: {e}")


class QueryRequest(BaseModel):
    """Request model for RAG queries."""
    query: str = Field(..., description="Question to ask about FastAPI")
    top_n: Optional[int] = Field(5, description="Number of documents to retrieve")


class SourceInfo(BaseModel):
    """Source information for citations."""
    id: str
    source: str
    breadcrumb: str
    similarity: float


class RAGResponse(BaseModel):
    """Response model for RAG queries."""
    query: str
    answer: str
    sources: list[SourceInfo]
    documents_retrieved: int
    context_length: int
    model: str
    tokens_used: int
    error: Optional[str] = None


class RAGAPI:
    """FastAPI application for RAG queries."""
    
    def __init__(self, config_path: Optional[str] = None, environment: str = "development"):
        """
        Initialize RAG API.
        
        Args:
            config_path: Path to configuration directory
            environment: Environment name (development, production)
        """
        # Load environment variables
        load_dotenv()
        
        # Initialize configuration
        self.config = Config(config_path=config_path, environment=environment)
        
        # Initialize RAG engine
        metadata_file = Path(self.config.ingestion_output_dir) / "metadata_lookup.json"
        self.rag_engine = RAGEngine(self.config, str(metadata_file))
        
        # Initialize FastAPI app
        self.app = FastAPI(
            title="FastAPI Documentation RAG API",
            description="Query FastAPI documentation using RAG with Vertex AI Vector Search and Gemini",
            version="1.0.0",
            redoc_url="/redoc",
            openapi_url="/openapi.json",
            contact={
                "name": "FastAPI Documentation RAG",
                "url": "http://localhost:8000"
            },
            license_info={
                "name": "MIT",
                "url": "https://opensource.org/licenses/MIT"
            }
        )
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["GET", "POST"],
            allow_headers=["*"],
        )
        
        # Setup routes
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup API routes."""
        
        @self.app.get("/", tags=["root"])
        async def root():
            return {
                "message": "FastAPI Documentation RAG API",
                "version": "1.0.0",
                "endpoints": {
                    "query": "/query",
                    "health": "/health",
                    "docs": "/docs"
                }
            }
        
        @self.app.get("/health", tags=["health"])
        async def health():
            return {"status": "healthy", "service": "rag-api"}
        
        @self.app.post("/query", response_model=RAGResponse, tags=["query"])
        async def query(request: QueryRequest):
            logger = None
            try:
                # Create logger for this request if logging is enabled
                if self.config.get("logging.enabled", True):
                    log_dir = self.config.get("logging.log_dir", "./output/logs")
                    logger = create_query_logger(log_dir=log_dir)
                    logger.log_request_start(request.query, request.top_n, request.dict())
                
                # Generate answer using RAG engine
                result = self.rag_engine.generate_answer(request.query, top_n=request.top_n, logger=logger)
                
                # Convert sources to SourceInfo objects
                sources = []
                similar_docs = result.get('similar_docs', [])
                
                for doc in similar_docs:
                    doc_id = doc.get("id", "")
                    metadata = self.rag_engine.metadata_lookup.get(doc_id, {})
                    
                    sources.append(SourceInfo(
                        id=doc_id,
                        source=metadata.get('source', 'Unknown source'),
                        breadcrumb=metadata.get('breadcrumb', ''),
                        similarity=float(doc.get('similarity', 0.0))
                    ))
                
                response_data = RAGResponse(
                    query=request.query,
                    answer=result.get('answer', ''),
                    sources=sources,
                    documents_retrieved=result.get('documents_retrieved', 0),
                    context_length=result.get('context_length', 0),
                    model=result.get('model', ''),
                    tokens_used=result.get('tokens_used', 0),
                    error=result.get('error')
                )
                
                if logger:
                    logger.log_request_complete(response_data.dict())
                
                return response_data
                
            except Exception as e:
                if logger:
                    logger.log_error("API_ENDPOINT", e, {"request": request.dict()})
                raise HTTPException(
                    status_code=500,
                    detail=f"Error processing query: {str(e)}"
                )
            finally:
                if logger:
                    logger.close()
    
    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """
        Run the FastAPI application.
        
        Args:
            host: Host to bind to
            port: Port to bind to
        """
        import uvicorn
        
        print(f"Starting FastAPI Documentation RAG API")
        print(f"Environment: {self.config.environment}")
        print(f"Host: {host}:{port}")
        
        uvicorn.run(
            self.app,
            host=host,
            port=port,
            log_level="info"
        )
