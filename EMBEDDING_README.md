# FastAPI Documentation RAG - Embedding Layer

This document describes how to generate embeddings for the processed document chunks using Vertex AI.

## Prerequisites

1. **Google Cloud Project**: Set up a GCP project with Vertex AI API enabled
2. **Service Account**: Create a service account with Vertex AI permissions
3. **Authentication**: Download the service account key file

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Required libraries for embedding:
- `google-cloud-aiplatform>=1.35.0`
- `python-dotenv>=1.0.0`
- `vertexai>=1.0.0`

### 2. Configure Environment Variables

Edit the `.env` file and replace the placeholders:

```bash
GCP_PROJECT_ID=your-actual-project-id
GCP_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/service-account-key.json
```

### 3. Create Service Account

1. **Go to GCP Console**: https://console.cloud.google.com/
2. **Navigate to IAM & Admin** → **Service Accounts**
3. **Click "Create Service Account"**
4. **Enter service account details**:
   - Name: `vertex-ai-user`
   - Description: `Service account for Vertex AI embeddings`
5. **Click "Create and Continue"**
6. **Grant permissions**: Select "Vertex AI User" role
7. **Click "Continue" and "Done"**
8. **Download JSON key**:
   - Find your service account in the list
   - Click on the service account name
   - Go to "Keys" tab
   - Click "Add Key" → "Create new key"
   - Select "JSON" and click "Create"
   - Save the downloaded JSON file securely
9. **Update .env file** with the path to your JSON key file

### 4. Enable Vertex AI API

In your GCP project, enable the Vertex AI API:
```bash
gcloud services enable aiplatform.googleapis.com --project=your-project-id
```

Or enable it through the GCP Console:
1. Go to APIs & Services → Library
2. Search for "Vertex AI API"
3. Click "Enable"

## Usage

### Basic Usage

Generate embeddings using default settings:

```bash
python scripts/embed.py
```

### Advanced Usage

Customize the embedding generation:

```bash
python scripts/embed.py \
  --chunks output/ingestion/processed_chunks.jsonl \
  --output output/embedding/vector_index_upload.jsonl \
  --batch-size 50 \
  --model text-embedding-004 \
  --delay 0.2
```

### Command Line Arguments

- `--chunks`: Path to processed chunks file (default: `output/ingestion/processed_chunks.jsonl`)
- `--output`: Path to output embeddings file (default: `output/embedding/vector_index_upload.jsonl`)
- `--batch-size`: Number of chunks to process per batch (default: 50)
- `--model`: Vertex AI embedding model (default: `text-embedding-004`)
- `--delay`: Delay between batches in seconds (default: 0.2)

## Output Format

The script generates a JSONL file with the following format:

```json
{"id": "fastapi_0", "embedding": [0.1234, -0.5678, 0.9012, ...]}
{"id": "fastapi_1", "embedding": [0.2345, -0.6789, 0.0123, ...]}
...
```

Each line contains:
- `id`: The chunk identifier from the ingestion pipeline
- `embedding`: 768-dimensional float array (for text-embedding-004)

## Rate Limiting

The script includes built-in rate limiting:
- Processes chunks in batches of 50 (configurable)
- 0.2 second delay between batches (configurable)
- Progress tracking with percentage completion

## Security

- Service account credentials are loaded from environment variables
- `.env` file is excluded from version control via `.gitignore`
- All JSON files are excluded from version control to protect sensitive data

## Troubleshooting

### Common Issues

1. **Missing Environment Variables**
   ```
   Error: Please set GCP_PROJECT_ID in .env file
   ```
   Solution: Update `.env` with your actual GCP project ID

2. **Invalid Service Account Key Path**
   ```
   Error: Please set GOOGLE_APPLICATION_CREDENTIALS to valid path in .env file
   ```
   Solution: Ensure the service account JSON key file exists at the specified path

3. **Service Account Permissions**
   ```
   Error: 403 Permission denied
   ```
   Solution: Ensure your service account has the "Vertex AI User" role

4. **Vertex AI API Not Enabled**
   ```
   Error: 403 Permission denied or API not enabled
   ```
   Solution: Enable Vertex AI API in your GCP project

5. **Missing Dependencies**
   ```
   Missing required dependency: No module named 'vertexai'
   ```
   Solution: Install dependencies with `pip install -r requirements.txt`

### Performance Tips

- Adjust `--batch-size` based on your quota limits (max: 100)
- Increase `--delay` if you encounter rate limit errors
- Monitor your GCP usage to avoid unexpected costs

## Example Output

```
Initializing Vertex AI...
Project: my-gcp-project
Location: us-central1
Loading embedding model: text-embedding-004
Loading chunks from: output/ingestion/processed_chunks.jsonl
Loaded 2278 chunks
Processing 2278 chunks in batches of 50...
Batch 1 complete. 50/2278 chunks embedded (2.2%)...
Batch 2 complete. 100/2278 chunks embedded (4.4%)...
...
Batch 46 complete. 2278/2278 chunks embedded (100.0%)...
Saving embeddings to: output/embedding/vector_index_upload.jsonl
Embedding generation completed!
Generated 2278 embeddings
Output saved to: output/embedding/vector_index_upload.jsonl
```

## Next Steps

After generating embeddings, you can:
1. Upload the vector index to a vector database (Pinecone, Weaviate, etc.)
2. Implement semantic search functionality
3. Build a RAG application using the embeddings and original chunks
