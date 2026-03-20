# FastAPI Documentation RAG

A Retrieval-Augmented Generation (RAG) system that combines vector search with generative AI to provide intelligent querying of FastAPI documentation.

## 🏗️ Global Architecture

The FastAPI Documentation RAG system implements a modular architecture that processes documentation through distinct stages, each utilizing specific AI/ML models and frameworks:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Raw Docs      │ →  │  Ingestion       │ →  │  Processed      │
│   (Markdown)    │    │  Pipeline        │    │  Chunks         │
│                 │    │                  │    │                 │
│ LangChain       │    │ Strategy Pattern │    │ JSONL Storage   │
│ Text Splitters  │    │ Quality Filters  │    │ Metadata        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                        │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   User Query    │ ←  │  RAG Query       │ ←  │  Vector         │
│   (Questions)   │    │  System          │    │  Embeddings     │
│                 │    │                  │    │                 │
│ FastAPI REST    │    │ Modular Classes  │    │ Vertex AI       │
│ Pydantic        │    │ Error Handling   │    │ text-embedding-004
└─────────────────┘    └──────────────────┘    └─────────────────┘
        │                       │                       │
        │              ┌──────────────────┐             │
        └─────────────►│  Gemini AI       │◀───────────┘
                       │  (Answer Gen)     │
                       │                  │
                       │ gemini-2.5-flash │
                       │ Context Window   │
                       └──────────────────┘
```

## AI/ML Models & Frameworks

### Core AI Models

#### **Embedding Model: Vertex AI text-embedding-004**
- **Dimensions**: 768-dimensional vectors
- **Provider**: Google Vertex AI
- **Characteristics**: High-quality semantic embeddings optimized for document similarity
- **Usage**: Converts document chunks and user queries into vector representations
- **Integration**: Accessed via Vertex AI API with rate limiting and batch processing

#### **Generative Model: Gemini 2.5 Flash**
- **Primary Model**: gemini-2.5-flash (main)
- **Context Window**: Configurable (default 4096 tokens)
- **Temperature**: 0.1 (focused, deterministic responses)
- **Usage**: Generates answers based on retrieved document context
- **Features**: Source citation, context-aware responses, error recovery

### Processing Frameworks

#### **LangChain Ecosystem**
- **Document Processing**: `MarkdownHeaderTextSplitter` for hierarchical chunking
- **Text Splitters**: Header-based splitting with context preservation
- **Document Objects**: LangChain `Document` class for structured content
- **Integration**: Seamless integration with custom processing pipeline

#### **FastAPI Framework**
- **API Framework**: High-performance async web framework
- **Validation**: Pydantic models for request/response validation
- **Documentation**: Automatic OpenAPI/Swagger generation
- **Middleware**: CORS support, error handling, structured responses

#### **Google Cloud Vertex AI**
- **Vector Search**: Managed vector database with HNSW indexing
- **Embedding API**: text-embedding-004 model access
- **Authentication**: Service account-based authentication
- **Scalability**: Auto-scaling infrastructure with regional endpoints

## 📋 Component Architecture & Implementation

### 1. **Ingestion Pipeline** 
**Implementation**: `RAGPipeline` class in `src/FastAPIDocsRAG/core/pipeline.py`

**Processing Frameworks Used**:
- **LangChain**: Document loading and hierarchical text splitting
- **Custom Processors**: Code reference extraction and content cleaning
- **Strategy Pattern**: Pluggable quality filtering and metadata enhancement

**Key Classes**:
- `MarkdownProcessor`: File loading and basic parsing
- `DocumentProcessor`: LangChain-based document splitting
- `DataCleaner`: Content enhancement and code extraction
- `MetadataExtractor`: MkDocs navigation parsing

**Details**: See [INGESTION_PIPELINE.md](INGESTION_PIPELINE.md)

### 2. **Embedding Generation**
**Implementation**: Script-based processing in `scripts/embed.py`

**AI Model Integration**:
- **Vertex AI text-embedding-004**: 768-dimensional vector generation
- **Batch Processing**: Configurable batch sizes with API rate limiting
- **Error Handling**: Retry logic and graceful degradation

**Framework Components**:
- **Vertex AI SDK**: Python client for embedding generation
- **JSONL Storage**: Efficient file-based storage format
- **Progress Tracking**: Real-time processing feedback

**Details**: See [EMBEDDING_README.md](EMBEDDING_README.md)

### 3. **RAG Query Engine**
**Implementation**: Modular classes in `src/FastAPIDocsRAG/query/`

**AI Model Architecture**:
- **Vector Search**: Vertex AI Vector Search with semantic similarity
- **Generative AI**: Gemini 2.5 Flash with context optimization
- **Fallback Logic**: Automatic model switching on failures

**Framework Integration**:
- **RAGEngine**: Main orchestration with lazy initialization
- **VectorSearchClient**: Vertex AI Vector Search abstraction
- **GeminiClient**: Gemini AI with prompt engineering

**Details**: See [RAG_QUERY_README.md](RAG_QUERY_README.md)

### 4. **API Layer**
**Implementation**: FastAPI application in `src/FastAPIDocsRAG/api/rag_api.py`

**Framework Components**:
- **FastAPI**: Async web framework with automatic documentation
- **Pydantic**: Request/response validation and serialization
- **CORS Middleware**: Cross-origin request support
- **Error Handling**: Structured HTTP error responses

**Integration Patterns**:
- **Dependency Injection**: RAGEngine injection into API endpoints
- **Model Validation**: Pydantic models for type safety
- **Response Formatting**: Structured JSON responses with metadata

**Details**: See [API_README.md](API_README.md)

## Framework Integration Architecture

### Model Orchestration Pattern
```python
# Embedding Generation Flow
Vertex AI text-embedding-004 → Vector Embeddings → Vertex AI Vector Search

# Query Processing Flow  
User Query → Embedding Generation → Vector Search → Context Retrieval → Gemini AI → Response
```

### Framework Dependencies
- **LangChain**: Document processing foundation
- **Vertex AI**: AI model hosting and vector search
- **FastAPI**: Web service framework
- **Pydantic**: Data validation layer
- **Python-dotenv**: Configuration management

### Data Flow Architecture
```
Markdown Files → LangChain Processors → Chunks → Vertex AI Embeddings → Vector Index
                                                                                ↑
User Query → FastAPI Endpoint → Vertex AI Search → Context → Gemini AI → Response
```

## 📊 Query Logs & Monitoring

The system automatically logs detailed query information to help with debugging and performance monitoring:

### Log Location
- **Directory**: `output/logs/`
- **Format**: Timestamped JSON log files (e.g., `query-20260319-175223.log`)

### Example Log Entry
```json
{
  "timestamp": "2026-03-19T17:52:23.857738",
  "elapsed_seconds": 0.002,
  "stage": "REQUEST_START",
  "message": "Processing query: How do I create a simple FastAPI application?...",
  "data": {
    "query": "How do I create a simple FastAPI application?",
    "top_n": 5
  }
}
```

### Log Stages
- **REQUEST_START**: Initial query processing
- **EMBEDDING_GENERATION**: Vector embedding creation
- **VECTOR_SEARCH_START**: Document similarity search
- **CONTEXT_ASSEMBLY**: Retrieved document context assembly
- **GEMINI_GENERATION_START**: AI answer generation
- **GEMINI_CALL_COMPLETE**: Final response generation

### Performance Metrics
Each log entry includes timing information to help track:
- Embedding generation time
- Vector search latency
- Context assembly duration
- Total query processing time

Use these logs to analyze query patterns, identify performance bottlenecks, and debug issues with specific queries.

## Architecture Documentation

| Document | Focus | Framework/Model Coverage |
|----------|-------|--------------------------|
| [INGESTION_PIPELINE.md](INGESTION_PIPELINE.md) | Document processing implementation | LangChain, custom processors |
| [EMBEDDING_README.md](EMBEDDING_README.md) | Vector embedding implementation | Vertex AI text-embedding-004 |
| [RAG_QUERY_README.md](RAG_QUERY_README.md) | RAG query system implementation | Vertex AI Search, Gemini AI |
| [API_README.md](API_README.md) | REST API implementation | FastAPI, Pydantic |

## Architecture Evolution

### Model & Framework Enhancement Roadmap

**Phase 1: Model Optimization**
1. **Multi-Model Support**: Support for alternative embedding models
2. **Context Optimization**: Advanced prompt engineering for Gemini
3. **Performance Tuning**: Model-specific parameter optimization

**Phase 2: Framework Enhancement**
1. **Advanced LangChain**: Deeper integration with LangChain ecosystem
2. **Async Processing**: Full async pipeline implementation
3. **Model Versioning**: Support for multiple model versions

**Phase 3: Architecture Evolution**
1. **Multi-Cloud**: Support for AWS/Azure AI models
2. **Custom Models**: Integration with fine-tuned models
3. **Framework Abstraction**: Provider-agnostic model interface

---

**Architecture documentation focusing on AI/ML models, frameworks, and global system design**
