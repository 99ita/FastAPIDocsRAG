"""
Vertex AI Vector Search client for finding similar document embeddings.
"""

import os
from typing import List, Dict, Any, Optional

try:
    from dotenv import load_dotenv
    import vertexai
    from vertexai.language_models import TextEmbeddingModel
    from google.oauth2 import service_account
    from google.cloud import aiplatform
    from google.cloud import aiplatform_v1 as aiplatform_v1
except ImportError as e:
    print(f"Missing required dependency: {e}")
    print("Please install: pip install google-cloud-aiplatform python-dotenv google-auth")
    raise ImportError(f"Missing dependencies: {e}")


class VectorSearchClient:
    """Client for Vertex AI Vector Search operations."""
    
    def __init__(self, config):
        """
        Initialize Vector Search client.
        
        Args:
            config: Configuration object with GCP settings
        """
        self.config = config
        self.embedding_model = None
        vector_search_config = config.get("vector_search", {})
        self.index_endpoint = vector_search_config.get("endpoint")
        self.deployed_index_id = vector_search_config.get("deployed_index_id", "")
        self.dimensions = vector_search_config.get("dimensions", 768)
        self.top_k = vector_search_config.get("top_k", 5)
        self._index_client = None
        
    def _initialize_embedding_model(self):
        """Initialize embedding model for query conversion."""
        if not self.embedding_model:
            # Import here to avoid circular imports
            from vertexai.language_models import TextEmbeddingModel
            import os
            from dotenv import load_dotenv
            from google.oauth2 import service_account
            import vertexai
            
            # Initialize Vertex AI with credentials
            load_dotenv()
            project_id = os.getenv('GCP_PROJECT_ID')
            location = os.getenv('GCP_LOCATION')
            credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
            
            if not all([project_id, location, credentials_path]):
                raise ValueError("Missing GCP configuration. Please check .env file.")
            
            credentials = service_account.Credentials.from_service_account_file(credentials_path)
            vertexai.init(project=project_id, location=location, credentials=credentials)
            
            # Load embedding model
            self.embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-004")
            print("Embedding model initialized successfully")
    
    def _initialize_index_client(self):
        """Initialize Vertex AI Vector Search index client."""
        if not self._index_client:
            if not self.index_endpoint:
                raise ValueError("Vector search endpoint not configured. Please check config.")
            
            # Parse endpoint to extract project_id, location, and endpoint_id
            # Expected format: projects/PROJECT_ID/locations/LOCATION/indexEndpoints/ENDPOINT_ID
            endpoint_parts = self.index_endpoint.split('/')
            
            if len(endpoint_parts) < 6:
                raise ValueError(f"Invalid endpoint format: {self.index_endpoint}. Expected: projects/PROJECT_ID/locations/LOCATION/indexEndpoints/ENDPOINT_ID")
            
            project_id = endpoint_parts[1]  # fastapidocsrag
            location = endpoint_parts[3]    # us-central1  
            endpoint_id = endpoint_parts[5]  # 8943209877027684352 (correct index)
            
            print(f"Parsed endpoint - Project: {project_id}, Location: {location}, Endpoint ID: {endpoint_id}")
            
            # Initialize Vertex AI with credentials
            import os
            from dotenv import load_dotenv
            from google.oauth2 import service_account
            import vertexai
            
            load_dotenv()
            credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
            
            if not credentials_path:
                raise ValueError("GOOGLE_APPLICATION_CREDENTIALS not found in environment variables")
            
            credentials = service_account.Credentials.from_service_account_file(credentials_path)
            vertexai.init(project=project_id, location=location, credentials=credentials)
            
            # Create index endpoint client
            from google.cloud import aiplatform
            aiplatform.init(project=project_id, credentials=credentials)
            self._index_client = aiplatform.MatchingEngineIndexEndpoint(
                index_endpoint_name=self.index_endpoint  # Use full path
            )
    
    def query_to_embedding(self, query_text: str, logger=None) -> List[float]:
        """
        Convert query text to embedding vector.
        
        Args:
            query_text: The search query text
            logger: Optional QueryLogger instance
            
        Returns:
            768-dimensional embedding vector
        """
        self._initialize_embedding_model()
        
        try:
            if logger:
                logger.log_info("EMBEDDING_MODEL", "Initializing embedding model")
            
            embedding = self.embedding_model.get_embeddings([query_text])
            embedding_vector = embedding[0].values
            
            if logger:
                logger.log_embedding_generation(query_text, len(embedding_vector))
            
            return embedding_vector
        except Exception as e:
            if logger:
                logger.log_error("EMBEDDING_GENERATION", e, {"query_text": query_text})
            raise
    
    def find_neighbors(self, query_embedding: List[float], top_k: Optional[int] = None, logger=None) -> List[Dict[str, Any]]:
        """
        Find similar documents using vector search.
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return (overrides config)
            logger: Optional QueryLogger instance
            
        Returns:
            List of similar documents with IDs and similarity scores
        """
        if top_k is None:
            top_k = self.top_k
            
        try:
            if logger:
                logger.log_info("VECTOR_SEARCH", f"Searching for {top_k} neighbors")
            
            self._initialize_index_client()
            
            # Find neighbors using simplified raw list input with GA endpoint
            if logger:
                logger.log_info("VECTOR_SEARCH", "Sending query to Vector Search endpoint with simplified format")
            
            # Use the simplified format: queries as list of lists (raw float arrays)
            # This avoids protobuf compatibility issues by using the stable MatchNeighbor format
            queries_as_lists = [query_embedding]  # Format: [[0.1, 0.2, ...]]
            
            if logger:
                logger.log_info("VECTOR_SEARCH_DEBUG", "Query details", {
                    "query_embedding_length": len(query_embedding),
                    "query_embedding_sample": query_embedding[:5],  # First 5 values
                    "queries_format": str(type(queries_as_lists)),
                    "queries_length": len(queries_as_lists),
                    "deployed_index_id": self.deployed_index_id,
                    "top_k": top_k
                })
            
            try:
                # Use the GA endpoint with simplified query format
                response = self._index_client.find_neighbors(
                    deployed_index_id=self.deployed_index_id,
                    queries=queries_as_lists,  # Pass as list of lists, not complex objects
                    num_neighbors=top_k
                )
                
                # Debug: Log response structure
                if logger:
                    logger.log_info("VECTOR_SEARCH_DEBUG", "Raw response received", {
                        "response_type": str(type(response)),
                        "response_attributes": [attr for attr in dir(response) if not attr.startswith('_')],
                        "has_neighbors": hasattr(response, 'neighbors'),
                        "neighbors_value": getattr(response, 'neighbors', 'NOT_FOUND'),
                        "response_repr": str(response)[:200]  # First 200 chars
                    })
                
            except (AttributeError, TypeError) as e:
                if "DESCRIPTOR" in str(e) or "ProtoType" in str(e):
                    # Fallback to the v1 API directly if the wrapper still has issues
                    if logger:
                        logger.log_warning("VECTOR_SEARCH", "Wrapper API has protobuf issues, using direct v1 API", {"error": str(e)})
                    
                    # Use the v1 API directly with the stable format
                    client_options = {"api_endpoint": f"{location}-aiplatform.googleapis.com"}
                    v1_client = aiplatform_v1.MatchServiceClient(client_options=client_options)
                    
                    # Build the request using the stable v1 format
                    index_endpoint_path = f"projects/{project_id}/locations/{location}/indexEndpoints/{endpoint_id}"
                    
                    request = aiplatform_v1.FindNeighborsRequest(
                        index_endpoint=index_endpoint_path,
                        deployed_index_id=self.deployed_index_id,
                        queries=[
                            aiplatform_v1.FindNeighborsRequest.Query(
                                embedding=query_embedding,  # Direct list of floats
                                neighbor_count=top_k
                            )
                        ]
                    )
                    
                    response = v1_client.find_neighbors(request=request)
                else:
                    raise
            
            # Process response with enhanced debugging
            results = []
            
            if logger:
                logger.log_info("VECTOR_SEARCH_DEBUG", "Processing response", {
                    "response_type": str(type(response)),
                    "response_dir": [attr for attr in dir(response) if not attr.startswith('_')][:10]  # First 10 attributes
                })
            
            # Handle the actual response format: list of lists with MatchNeighbor objects
            if isinstance(response, list) and len(response) > 0:
                neighbors_list = response[0]  # First query results
                if logger:
                    logger.log_info("VECTOR_SEARCH_DEBUG", "Processing neighbor list", {
                        "neighbors_list_type": str(type(neighbors_list)),
                        "neighbors_list_length": len(neighbors_list) if hasattr(neighbors_list, '__len__') else 'NO_LEN',
                        "first_neighbor_type": str(type(neighbors_list[0])) if neighbors_list else 'EMPTY'
                    })
                
                for neighbor in neighbors_list:
                    result = {
                        "id": getattr(neighbor, 'id', f"doc_{len(results)}"),
                        "similarity": float(getattr(neighbor, 'distance', 0.0)),
                        "metadata": {}
                    }
                    results.append(result)
                    
                    if logger:
                        logger.log_info("VECTOR_SEARCH_DEBUG", "Processed neighbor", {
                            "neighbor_type": str(type(neighbor)),
                            "neighbor_id": result["id"],
                            "neighbor_similarity": result["similarity"],
                            "neighbor_attributes": [attr for attr in dir(neighbor) if not attr.startswith('_')][:5]
                        })
            
            # Try different response structures (fallback for other formats)
            elif hasattr(response, 'neighbors') and response.neighbors:
                if logger:
                    logger.log_info("VECTOR_SEARCH_DEBUG", "Found neighbors attribute", {
                        "neighbors_type": str(type(response.neighbors)),
                        "neighbors_length": len(response.neighbors) if hasattr(response.neighbors, '__len__') else 'NO_LEN',
                        "neighbors_first_item_type": str(type(response.neighbors[0])) if response.neighbors else 'EMPTY'
                    })
                
                # Handle different neighbor structures
                if isinstance(response.neighbors, list) and len(response.neighbors) > 0:
                    neighbors_list = response.neighbors[0]  # First query results
                    if logger:
                        logger.log_info("VECTOR_SEARCH_DEBUG", "Processing neighbor list", {
                            "neighbors_list_type": str(type(neighbors_list)),
                            "neighbors_list_length": len(neighbors_list) if hasattr(neighbors_list, '__len__') else 'NO_LEN',
                            "first_neighbor_type": str(type(neighbors_list[0])) if neighbors_list else 'EMPTY'
                        })
                    
                    for neighbor in neighbors_list:
                        result = {
                            "id": getattr(neighbor, 'id', f"doc_{len(results)}"),
                            "similarity": float(getattr(neighbor, 'distance', 0.0)),
                            "metadata": {}
                        }
                        results.append(result)
                        
                        if logger:
                            logger.log_info("VECTOR_SEARCH_DEBUG", "Processed neighbor", {
                                "neighbor_type": str(type(neighbor)),
                                "neighbor_id": result["id"],
                                "neighbor_similarity": result["similarity"],
                                "neighbor_attributes": [attr for attr in dir(neighbor) if not attr.startswith('_')][:5]
                            })
                            
                else:
                    if logger:
                        logger.log_warning("VECTOR_SEARCH_DEBUG", "Unexpected neighbors structure", {
                            "neighbors_value": str(response.neighbors)[:200]
                        })
            
            # Try alternative response structures
            elif hasattr(response, 'nearest_neighbors') and response.nearest_neighbors:
                if logger:
                    logger.log_info("VECTOR_SEARCH_DEBUG", "Found nearest_neighbors attribute")
                # Process alternative structure
            
            elif hasattr(response, 'matches') and response.matches:
                if logger:
                    logger.log_info("VECTOR_SEARCH_DEBUG", "Found matches attribute")
                # Process alternative structure
            
            else:
                if logger:
                    logger.log_warning("VECTOR_SEARCH_DEBUG", "No recognized result structure found", {
                        "available_attributes": [attr for attr in dir(response) if not attr.startswith('_')],
                        "response_str": str(response)[:300]
                    })
            
            if logger:
                logger.log_info("VECTOR_SEARCH_DEBUG", "Final results", {
                    "results_count": len(results),
                    "results_sample": results[:2] if results else []
                })
            
            if logger:
                logger.log_document_retrieval(len(results), results)
            
            return results
            
        except Exception as e:
            if logger:
                logger.log_error("VECTOR_SEARCH", e, {"top_k": top_k, "embedding_dim": len(query_embedding)})
            # Return empty results instead of raising exception to allow continued execution
            return []
