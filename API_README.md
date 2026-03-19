# FastAPI Documentation RAG API

This document describes the REST API for querying FastAPI documentation using RAG (Retrieval-Augmented Generation).

## Overview

The RAG API provides HTTP endpoints for asking questions about FastAPI documentation. It combines vector search with generative AI to provide accurate, source-cited answers.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, no authentication is required. The API is open for development use.

## Endpoints

### GET /

Root endpoint with API information.

**Response:**
```json
{
    "message": "FastAPI Documentation RAG API",
    "version": "1.0.0",
    "endpoints": {
        "query": "/query",
        "health": "/health",
        "docs": "/docs"
    }
}
```

### GET /health

Health check endpoint.

**Response:**
```json
{
    "status": "healthy",
    "service": "rag-api"
}
```

### GET /docs

Auto-generated OpenAPI documentation (Swagger UI).

**Response:**
Interactive API documentation interface.

### POST /query

Main query endpoint for RAG functionality.

**Request Body:**
```json
{
    "query": "How do I create a FastAPI endpoint?",
    "top_n": 5
}
```

**Response:**
```json
{
    "query": "How do I create a FastAPI endpoint?",
    "answer": "To create a FastAPI endpoint, you use @app decorator...",
    "similar_docs": [
        {
            "id": "fastapi_123",
            "source": "docs/tutorial/getting-started.md",
            "breadcrumb": "Getting Started > First Steps",
            "similarity": 0.95
        }
    ],
    "documents_retrieved": 5,
    "context_length": 2847,
    "model": "gemini-3.1-flash-lite-preview",
    "tokens_used": 156
}
```

## Usage Examples

### Basic Query

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is dependency injection?"
  }'
```

### Python Client

```python
import requests

response = requests.post(
    "http://localhost:8000/query",
    json={"query": "How does middleware work?", "top_n": 3}
)

result = response.json()
print(f"Answer: {result['answer']}")
print(f"Similar docs: {len(result.get('similar_docs', []))}")
```

### JavaScript Client

```javascript
async function queryFastAPI(question) {
    const response = await fetch('http://localhost:8000/query', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            query: question,
            top_n: 5
        })
    });
    
    const result = await response.json();
    console.log('Answer:', result.answer);
    console.log('Similar docs:', result.similar_docs);
}

// Usage
queryFastAPI('What are async views?');
```

### Testing with Swagger UI

1. **Start server**: `python scripts/serve.py`
2. **Open Swagger**: Navigate to `http://localhost:8000/docs`
3. **Try queries**: Use the "Try it out" feature in Swagger UI
4. **View responses**: Check the response body and status codes

### Advanced Testing

```bash
# Test with different top_n values
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is dependency injection?", "top_n": 10}'

# Test error handling
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "", "top_n": 5}'
```

## Request/Response Models

### QueryRequest

```typescript
interface QueryRequest {
    query: string;
    top_n?: number;  // Optional, defaults to 5
}
```

### SourceInfo

```typescript
interface SourceInfo {
    id: string;
    source: string;
    breadcrumb: string;
    similarity: number;
}
```

### RAGResponse

```typescript
interface RAGResponse {
    query: string;
    answer: string;
    similar_docs: SourceInfo[];
    documents_retrieved: number;
    context_length: number;
    model: string;
    tokens_used: number;
    error?: string;  // Only present on errors
}
```

## Error Handling

### HTTP Status Codes

- **200 OK**: Request successful
- **400 Bad Request**: Invalid request format
- **500 Internal Server Error**: Processing error

### Error Response Format

```json
{
    "query": "original question",
    "answer": "",
    "sources": [],
    "error": "Error processing query: Connection timeout"
}
```

## Configuration

The API uses environment variables for configuration:

### Development (.env)

```bash
GCP_PROJECT_ID=your-project-id
GCP_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
```

### Configuration Files

- `config/development.yaml` - Development settings
- `config/production.yaml` - Production settings

## Vector Search Index

You need a Vertex AI Vector Search index deployed and accessible.

**Get your endpoint from GCP Console:**
1. Go to [Vertex AI Console](https://console.cloud.google.com/vertex-ai)
2. Navigate to "Vector Search" → "Index Endpoints"
3. Find your index endpoint (format: `projects/PROJECT_ID/locations/LOCATION/indexEndpoints/ENDPOINT_ID`)
4. Update your configuration files with the full endpoint path

**Update configuration files:**
- `config/development.yaml`: Set the full endpoint path in `vector_search.endpoint`
- `config/production.yaml`: Set the full endpoint path in `vector_search.endpoint`

**Example endpoint:**
```yaml
vector_search:
  endpoint: "projects/fastapidocsrag/locations/us-central1/indexEndpoints/YOUR_ENDPOINT_ID"
```

## Running the Server

### Development

```bash
python scripts/serve.py --reload
```

### Production

```bash
python scripts/serve.py --host 0.0.0.0 --port 8000
```

### Custom Configuration

```bash
python scripts/serve.py --environment production --config /path/to/config
```

## Architecture

The API follows this architecture:

1. **Request Reception**: FastAPI receives HTTP request
2. **Query Processing**: Question converted to embedding vector
3. **Vector Search**: Finds similar documents using Vertex AI
4. **Metadata Lookup**: Retrieves document information
5. **Context Formatting**: Structures retrieved information for LLM
6. **Answer Generation**: Gemini generates response with context
7. **Source Citation**: Extracts and returns source references
8. **Response Delivery**: Returns structured JSON response

## Rate Limiting

Currently no rate limiting is implemented. Consider adding:
- Request rate limits
- User authentication
- Request quotas

## Security Considerations

For production deployment, consider:
- API key authentication
- Request validation
- Input sanitization
- CORS configuration
- HTTPS enforcement
- Request logging
