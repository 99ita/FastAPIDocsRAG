# FastAPI Documentation RAG Query System

This document describes how to use the RAG query system to ask questions about FastAPI documentation.

## Overview

The RAG (Retrieval-Augmented Generation) query system combines:
- **Vector Search**: Finds relevant document chunks using Vertex AI embeddings
- **Gemini AI**: Generates answers using retrieved context
- **Metadata Lookup**: Fast access to document information and sources

## Prerequisites

### 1. Configuration

Update your `.env` file with your GCP settings:

```bash
GCP_PROJECT_ID=your-gcp-project-id
GCP_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/service-account-key.json
```

### 2. Dependencies

Install required packages:

```bash
pip install -r requirements.txt
```

Key dependencies:
- `google-cloud-aiplatform>=1.35.0` (Vertex AI)
- `google-generativeai>=0.3.0` (Gemini)
- `google-auth>=2.0.0` (Authentication)
- `python-dotenv>=1.0.0` (Environment variables)

### 3. Vector Search Index

Ensure you have a Vertex AI Vector Search index deployed and accessible. Update the `vector_search.endpoint` in your configuration files:

**Development (`config/development.yaml`):**
```yaml
vector_search:
  endpoint: "your-index-endpoint"
  dimensions: 768
  top_k: 5
```

**Production (`config/production.yaml`):**
```yaml
vector_search:
  endpoint: "your-index-endpoint"
  dimensions: 768
  top_k: 5
```

## Usage

### Basic Query

Ask a question about FastAPI:

```bash
python scripts/query.py "How do I create a FastAPI endpoint?"
```

### Advanced Options

Specify number of documents to retrieve:

```bash
python scripts/query.py "What is dependency injection?" --top-n 10
```

Use production configuration:

```bash
python scripts/query.py "How does middleware work?" --environment production
```

Custom configuration directory:

```bash
python scripts/query.py "What are async views?" --config /path/to/config
```

## Output Format

The query system provides:

### Answer Section
- AI-generated response based on retrieved documentation
- Uses Gemini 1.5 Flash model for fast responses

### Sources Section
- List of document sources used in the answer
- Shows file paths and navigation breadcrumbs
- Enables fact-checking and further reading

### Metadata Section
- Number of documents retrieved
- Context length used
- Model version and tokens consumed
- Error information if any issues occur

## Example Usage

```bash
$ python scripts/query.py "How do I implement authentication?"

============================================================
ANSWER:
============================================================
To implement authentication in FastAPI, you can use OAuth2 with JWT tokens. Here's a basic approach:

1. Install required dependencies:
   pip install python-jose[cryptography] passlib[bcrypt]

2. Create authentication dependencies:
   from fastapi import Depends
   from fastapi.security import OAuth2PasswordBearer
   from jose import JWTError, jwt
   from passlib.context import CryptContext

3. Implement JWT token generation and validation...

============================================================
SOURCES:
============================================================
1. docs/tutorial/security/tutorial001.md
2. docs/tutorial/security/tutorial002.md
3. docs/advanced/security/oauth2-jwt.md

============================================================
METADATA:
============================================================
Documents retrieved: 5
Context length: 2847 characters
Model used: gemini-1.5-flash
Tokens used: 156
```

## Configuration Options

### Vector Search Settings
- `vector_search.dimensions`: Embedding dimensions (default: 768)
- `vector_search.top_k`: Number of results to return (default: 5)
- `vector_search.endpoint`: Your Vector Search index endpoint

### Gemini Settings
- `gemini.model`: Model name (default: gemini-1.5-flash)
- `gemini.max_tokens`: Maximum response tokens (default: 4096)
- `gemini.temperature`: Response randomness (default: 0.1)

## Troubleshooting

### Common Issues

1. **Missing GCP Configuration**
   ```
   Error: Missing GCP configuration. Please check .env file.
   ```
   Solution: Ensure GCP_PROJECT_ID, GCP_LOCATION, and GCP_BUCKET_NAME are set in .env

2. **Vector Search Connection Failed**
   ```
   Error: Error searching vector index: Connection refused
   ```
   Solution: Check vector_search.endpoint in configuration and ensure index is accessible

3. **Metadata File Not Found**
   ```
   Warning: Metadata file not found: output/ingestion/metadata_lookup.json
   ```
   Solution: Run the ingestion pipeline first to generate metadata

4. **Authentication Errors**
   ```
   Error: Missing dependencies: No module named 'vertexai'
   ```
   Solution: Install with `pip install -r requirements.txt`

## Architecture

The RAG system follows this flow:

1. **Query Processing**: User question → embedding vector
2. **Vector Search**: Embedding → similar document retrieval
3. **Metadata Lookup**: Document IDs → full metadata (sources, breadcrumbs)
4. **Context Formatting**: Retrieved docs → structured context string
5. **Answer Generation**: Context + query → Gemini response
6. **Source Extraction**: Response → cited sources list

This ensures answers are based on actual documentation content while providing clear attribution to source materials.
