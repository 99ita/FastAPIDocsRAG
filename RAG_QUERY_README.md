# FastAPI Documentation RAG - Query Implementation

## Overview

The query system is implemented in the `src/FastAPIDocsRAG/query/` directory as a modular RAG (Retrieval-Augmented Generation) engine that combines vector search with generative AI to provide accurate, source-cited answers to FastAPI documentation questions.

## Query Implementation Architecture

### Core Components (`src/FastAPIDocsRAG/query/`)

The query system consists of three main classes that work together:

```
User Query → RAGEngine → VectorSearchClient → GeminiClient → Response
     │              │              │              │           │
   Script/      Orchestration   Vertex AI      LLM       Formatted
   API           Logic           Search        Generation  JSON
```

### Implementation Details

#### RAGEngine (`rag_engine.py`)

**Purpose**: Main orchestration class that coordinates the entire RAG pipeline

**Key Methods**:
```python
class RAGEngine:
    def __init__(self, config, metadata_file: str = None):
        # Initialize with configuration and metadata lookup
        self.metadata_lookup = {}
        self._vertexai_initialized = False
    
    def get_relevant_context(self, query_text: str, top_n: int = 5) -> Dict[str, Any]:
        # Retrieve relevant documents using vector search
        # Enhance results with metadata from lookup table
        # Return formatted context with source information
    
    def query(self, query_text: str, top_n: int = 5, logger=None) -> Dict[str, Any]:
        # Complete RAG pipeline: search → context → generation
        # Returns structured response with answer and sources
```

**Architecture Features**:
- **Lazy Initialization**: Vector and Gemini clients created only when needed
- **Metadata Enhancement**: Loads metadata lookup for rich source information
- **Vertex AI Management**: Single initialization for all Vertex AI components
- **Error Handling**: Graceful fallbacks for missing components

#### VectorSearchClient (`vector_search.py`)

**Purpose**: Interfaces with Vertex AI Vector Search for document retrieval

**Key Methods**:
```python
class VectorSearchClient:
    def __init__(self, config):
        # Initialize with vector search configuration
        self.index_endpoint = config.get("endpoint")
        self.dimensions = config.get("dimensions", 768)
        self.top_k = config.get("top_k", 5)
    
    def search_similar(self, query_text: str, top_n: int = None) -> List[Dict[str, Any]]:
        # Convert query to embedding using Vertex AI
        # Search vector index for similar documents
        # Return ranked results with similarity scores
    
    def _initialize_embedding_model(self):
        # Initialize text-embedding-004 model for queries
        # Handle Vertex AI authentication and configuration
```

**Architecture Features**:
- **Embedding Generation**: Uses Vertex AI text-embedding-004 model
- **Vector Search Integration**: Interfaces with Vertex AI Vector Search index
- **Configurable Parameters**: Adjustable top-k and dimensions
- **Error Recovery**: Handles API failures gracefully

#### GeminiClient (`gemini_client.py`)

**Purpose**: Interfaces with Google's Gemini AI for answer generation

**Key Methods**:
```python
class GeminiClient:
    def __init__(self, config):
        # Initialize with Gemini configuration
        self.primary_model = config.get("model", "gemini-2.5-flash")
        self.fallback_model = "gemini-2.0-flash-exp"
        self.max_tokens = config.get("max_tokens", 4096)
    
    def generate_answer(self, query: str, context: str, logger=None) -> Dict[str, Any]:
        # Construct prompt with query and retrieved context
        # Generate answer using Gemini model
        # Handle fallback to backup model if needed
        # Return structured response with metadata
    
    def _initialize_model(self):
        # Initialize Gemini model with fallback logic
        # Try primary model first, then fallback
        # Handle model availability and authentication
```

**Architecture Features**:
- **Model Fallback**: Automatic fallback to backup model on failures
- **Prompt Engineering**: Structured prompt construction with context
- **Configurable Parameters**: Adjustable temperature, max tokens
- **Error Handling**: Comprehensive error recovery and logging

### Query Processing Flow

#### Complete RAG Pipeline

1. **Query Reception**: `RAGEngine.query()` receives user query
2. **Vector Search**: `VectorSearchClient.search_similar()` finds relevant documents
3. **Context Building**: Documents formatted with metadata for LLM consumption
4. **Answer Generation**: `GeminiClient.generate_answer()` creates response
5. **Response Formatting**: Structured JSON with answer and source citations

#### Data Flow
```python
# Example query flow
rag_engine = RAGEngine(config, metadata_file="metadata_lookup.json")
response = rag_engine.query("How do I create a FastAPI endpoint?", top_n=5)

# Response structure
{
    "query": "How do I create a FastAPI endpoint?",
    "answer": "To create a FastAPI endpoint...",
    "sources": [
        {
            "id": "fastapi_123",
            "source": "docs/tutorial/first-steps.md",
            "breadcrumb": "Tutorial > First Steps",
            "similarity": 0.95
        }
    ],
    "documents_retrieved": 5,
    "context_length": 2847,
    "model": "gemini-2.5-flash",
    "tokens_used": 156
}
```

### Current Implementation Features

#### ✅ Implemented
- **Modular Design**: Separate classes for search, generation, and orchestration
- **Vertex AI Integration**: Full integration with Vector Search and Gemini
- **Metadata Enhancement**: Rich source information from metadata lookup
- **Error Handling**: Comprehensive error recovery and fallback mechanisms
- **Configuration Management**: Flexible configuration through config objects
- **Lazy Loading**: Efficient resource initialization

#### ❌ Not Implemented
- **Query Enhancement**: No query expansion or intent classification
- **Context Optimization**: Fixed context window management
- **Response Validation**: No quality assessment of generated answers
- **Performance Caching**: No query result caching
- **Advanced Analytics**: No query logging or performance metrics

### Usage Examples

#### Direct RAGEngine Usage
```python
from FastAPIDocsRAG.query.rag_engine import RAGEngine
from FastAPIDocsRAG.core.config import Config

# Initialize
config = Config(config_path="config", environment="development")
rag_engine = RAGEngine(config, metadata_file="output/ingestion/metadata_lookup.json")

# Query
response = rag_engine.query("What is dependency injection?", top_n=5)
print(f"Answer: {response['answer']}")
print(f"Sources: {len(response['sources'])}")
```

#### Individual Component Usage
```python
from FastAPIDocsRAG.query.vector_search import VectorSearchClient
from FastAPIDocsRAG.query.gemini_client import GeminiClient

# Vector search only
vector_client = VectorSearchClient(config)
results = vector_client.search_similar("FastAPI middleware", top_n=3)

# Gemini generation only
gemini_client = GeminiClient(config)
answer = gemini_client.generate_answer("Explain async/await", context_text)
```

### Configuration Requirements

#### Environment Variables
```bash
GCP_PROJECT_ID=your-gcp-project-id
GCP_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
```

#### Configuration Structure
```python
config = {
    "vector_search": {
        "endpoint": "projects/PROJECT_ID/locations/LOCATION/indexEndpoints/ENDPOINT_ID",
        "dimensions": 768,
        "top_k": 5
    },
    "gemini": {
        "model": "gemini-2.5-flash",
        "max_tokens": 4096,
        "temperature": 0.1
    },
    "logging": {
        "enabled": True,
        "log_dir": "./output/logs"
    }
}
```

### Architecture Evolution

#### Planned Improvements (Not Yet Implemented)

**Phase 1: Performance Enhancement**
1. **Query Caching**: Cache similar queries and results
2. **Parallel Processing**: Concurrent vector search and generation
3. **Connection Pooling**: Optimize Vertex AI client connections

**Phase 2: Advanced Features**
1. **Query Enhancement**: Intent classification and query expansion
2. **Context Optimization**: Intelligent context window management
3. **Response Validation**: Quality assessment of generated answers

**Phase 3: Scalability Enhancement**
1. **Multi-Model Support**: Support for multiple LLM models
2. **Advanced Analytics**: Query logging and performance metrics
3. **Batch Processing**: Handle multiple queries efficiently

---

**Current modular RAG implementation in `src/FastAPIDocsRAG/query/` with planned enhancements**
