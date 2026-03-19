# FastAPI Documentation RAG

A comprehensive Retrieval-Augmented Generation (RAG) system for querying FastAPI documentation using vector search and generative AI.

## 🚀 Overview

The FastAPI Documentation RAG system transforms raw FastAPI documentation into an intelligent question-answering system. It processes documentation files, generates vector embeddings, and uses Google's Vertex AI and Gemini models to provide accurate, source-cited answers to user questions.

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Raw Docs      │ →  │  Ingestion       │ →  │  Processed      │
│   (Markdown)    │    │  Pipeline        │    │  Chunks         │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                        │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   User Query    │ ←  │  RAG Query       │ ←  │  Vector         │
│   (Questions)   │    │  System          │    │  Embeddings     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
        │                       │                       │
        │              ┌──────────────────┐            │
        └─────────────►│  Gemini AI       │◀───────────┘
                       │  (Answer Gen)     │
                       └──────────────────┘
```

## 📋 Data Pipeline

The system follows a comprehensive data processing pipeline:

### 1. **Ingestion Pipeline** 
- **Input**: Raw FastAPI documentation (Markdown files)
- **Process**: Document loading, splitting, content enhancement, quality filtering
- **Output**: Enhanced chunks with rich metadata
- **Details**: See [INGESTION_PIPELINE.md](INGESTION_PIPELINE.md)

### 2. **Embedding Generation**
- **Input**: Processed document chunks
- **Process**: Vector embedding generation using Vertex AI
- **Output**: 768-dimensional embeddings for semantic search
- **Details**: See [EMBEDDING_README.md](EMBEDDING_README.md)

### 3. **Vector Search**
- **Input**: User query embeddings
- **Process**: Semantic similarity search in vector space
- **Output**: Most relevant document chunks
- **Technology**: Google Vertex AI Vector Search

### 4. **RAG Query System**
- **Input**: User question + retrieved documents
- **Process**: Context-aware answer generation
- **Output**: AI-generated responses with source citations
- **Details**: See [RAG_QUERY_README.md](RAG_QUERY_README.md)

### 5. **API Layer**
- **Input**: HTTP requests
- **Process**: RESTful API endpoints
- **Output**: Structured JSON responses
- **Details**: See [API_README.md](API_README.md)

### 6. **User Interface**
- **Input**: User interactions
- **Process**: Streamlit web interface
- **Output**: Interactive Q&A experience
- **Details**: See [UI_README.md](UI_README.md)

## 🚀 Quick Start

### Prerequisites

1. **Python 3.8+**
2. **Google Cloud Project** with Vertex AI API enabled
3. **Service Account** with Vertex AI permissions

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd FastAPIDocsRAG

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your GCP credentials
```

### Setup

1. **Configure Google Cloud**:
   ```bash
   gcloud services enable aiplatform.googleapis.com --project=your-project-id
   ```

2. **Set up Service Account**:
   - Create service account with "Vertex AI User" role
   - Download JSON key file
   - Update `.env` with key file path

3. **Deploy Vector Search Index**:
   - Create Vertex AI Vector Search index
   - Update `config/development.yaml` with endpoint

### Run the Complete Pipeline

```bash
# Step 1: Process documentation
python scripts/ingest.py

# Step 2: Generate embeddings
python scripts/embed.py

# Step 3: Start API server
python scripts/serve.py

# Step 4: Launch UI (in separate terminal)
streamlit run streamlit_ui.py
```

## 📖 Documentation

| Document | Description |
|----------|-------------|
| [INGESTION_PIPELINE.md](INGESTION_PIPELINE.md) | Detailed documentation processing pipeline |
| [EMBEDDING_README.md](EMBEDDING_README.md) | Vector embedding generation guide |
| [RAG_QUERY_README.md](RAG_QUERY_README.md) | Query system usage and configuration |
| [API_README.md](API_README.md) | REST API endpoints and examples |
| [UI_README.md](UI_README.md) | Streamlit interface guide |

## 💡 Usage Examples

### Command Line Query
```bash
python scripts/query.py "How do I create a FastAPI endpoint?"
```

### Python API Usage
```python
import requests

response = requests.post(
    "http://localhost:8000/query",
    json={"query": "What is dependency injection?", "top_n": 5}
)

result = response.json()
print(f"Answer: {result['answer']}")
```

### Interactive UI
Open `http://localhost:8501` in your browser to use the web interface.

## 🔧 Configuration

The system uses YAML configuration files:

- `config/development.yaml` - Development settings
- `config/production.yaml` - Production settings

Key configuration sections:
- `ingestion` - Document processing parameters
- `embeddings` - Embedding model settings
- `vector_search` - Vector search configuration
- `gemini` - AI model settings

## 📊 System Components

### Core Technologies
- **LangChain**: Document processing and text splitting
- **Vertex AI**: Vector embeddings and search
- **Gemini**: Answer generation
- **FastAPI**: REST API framework
- **Streamlit**: Web interface

### Data Flow
1. **Documentation Processing**: Smart chunking with context preservation
2. **Vector Indexing**: Semantic embeddings for similarity search
3. **Query Processing**: Context-aware answer generation
4. **Source Attribution**: Complete citation tracking

## 🛠️ Development

### Project Structure
```
FastAPIDocsRAG/
├── src/FastAPIDocsRAG/          # Core library
│   ├── api/                     # REST API endpoints
│   ├── core/                    # Pipeline orchestration
│   ├── ingestion/               # Document processing
│   └── query/                   # RAG query engine
├── scripts/                     # Command-line tools
├── config/                      # Configuration files
├── docs/                        # FastAPI documentation
└── streamlit_ui.py              # Web interface
```

### Running Tests
```bash
pytest tests/
```

### Code Quality
```bash
black src/ scripts/
isort src/ scripts/
flake8 src/ scripts/
```

## 🔒 Security

- Service account credentials loaded from environment variables
- No sensitive data stored in codebase
- Local API deployment by default
- Configurable CORS and authentication for production

## 📈 Performance

- **Processing**: Handles thousands of documentation pages
- **Search**: Sub-second semantic search
- **Generation**: Fast response times with Gemini Flash
- **Storage**: Efficient JSONL format for chunks and metadata

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For issues and questions:
1. Check the troubleshooting sections in specialized documentation
2. Verify Google Cloud configuration
3. Ensure all dependencies are installed
4. Check that Vector Search index is deployed

## 📄 License

[Add your license information here]

---

**Built with ❤️ for the FastAPI community**
