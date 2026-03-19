# FastAPI Documentation RAG UI

A Streamlit-based user interface for querying FastAPI documentation using the RAG (Retrieval-Augmented Generation) system.

## 🚀 Quick Start

### Step 1: Start the API Server
Open a terminal and run:
```bash
python -m FastAPIDocsRAG.api.rag_api
```
The API server will start at `http://localhost:8000`

### Step 2: Start the Streamlit UI
Open a second terminal and run:
```bash
streamlit run streamlit_ui.py --server.port 8501
```
The UI will be available at `http://localhost:8501`

### Alternative: Use run_ui.py (Background API)
If you want the API to run in the background:
```bash
python run_ui.py
```
This will start the API in background and then launch the Streamlit UI.

## 🎨 Features

### Main Interface
- **Query Input**: Large text area for asking questions about FastAPI
- **Number of Sources**: Slider to control how many documents to retrieve (1-10)
- **Real-time Search**: Get answers with source citations

### Sidebar Configuration
- **API URL**: Configure the RAG API endpoint
- **Query Parameters**: Adjust the number of sources to retrieve
- **Model Information**: View details about the underlying models

### Response Display
- **Answer**: Main response from the RAG system
- **Sources**: Expandable cards showing:
  - Document ID
  - Source file path
  - Breadcrumb navigation
  - Similarity score (color-coded)
- **Metrics**: Documents retrieved, context length, tokens used
- **Query History**: Last 5 queries with their answers

### Source Similarity Colors
- 🟢 **High** (≥0.9): Very relevant document
- 🟡 **Medium** (≥0.7): Moderately relevant
- 🔴 **Low** (<0.7): Less relevant

## 💡 Example Questions

Try these sample questions to test the system:

- "How do I create a simple FastAPI application?"
- "What is dependency injection in FastAPI?"
- "How do I add authentication to my FastAPI app?"
- "What are the different status codes I can use?"
- "How do I handle file uploads in FastAPI?"
- "What is the difference between Query and Path parameters?"
- "How do I create async endpoints in FastAPI?"

## 🔧 Technical Details

### API Endpoints
- **Health Check**: `GET /health`
- **Query**: `POST /query`

### Request Format
```json
{
  "query": "Your question here",
  "top_n": 5
}
```

### Response Format
```json
{
  "query": "Your question",
  "answer": "The generated answer",
  "sources": [
    {
      "id": "document_id",
      "source": "path/to/document",
      "breadcrumb": "navigation_path",
      "similarity": 0.95
    }
  ],
  "documents_retrieved": 5,
  "context_length": 2048,
  "model": "gemini-2.5-flash",
  "tokens_used": 256
}
```

## 🛠️ Troubleshooting

### API Connection Issues
1. **Make sure the API server is running**: Check that `python -m FastAPIDocsRAG.api.rag_api` is running
2. **Check the URL**: Verify the API URL in the sidebar matches your server
3. **Port conflicts**: Make sure ports 8000 and 8501 are available

### Environment Issues
1. **Check .env file**: Ensure GCP credentials are properly configured
2. **Dependencies**: Run `pip install -r requirements.txt` to install all dependencies
3. **Python version**: Ensure you're using Python 3.8+

### Performance Tips
1. **Reduce sources**: Lower the "Number of Sources" for faster responses
2. **Specific queries**: More detailed questions get better results
3. **Check similarity scores**: Higher similarity indicates more relevant results

## 📱 Mobile Support

The Streamlit UI is fully responsive and works on:
- Desktop browsers
- Tablets
- Mobile devices

## 🔒 Security

- The API runs locally by default
- No data is sent to external services (except Google Cloud APIs)
- Queries and responses are not stored permanently

## 📊 System Architecture

```
Streamlit UI (Port 8501)
    ↓ HTTP Request
RAG API (Port 8000)
    ↓
Vector Search + Gemini LLM
    ↓
FastAPI Documentation
```

## 🤝 Contributing

To improve the UI:
1. Modify `streamlit_ui.py` for UI changes
2. Update `run_ui.py` for startup behavior
3. Test both manual and automatic startup modes

## 📞 Support

If you encounter issues:
1. Check the terminal output for error messages
2. Verify all dependencies are installed
3. Ensure Google Cloud credentials are properly configured
4. Check that the Vector Search index is deployed and accessible
