"""
Gemini client for generating answers using retrieved context.
"""

import os
from typing import List, Dict, Any, Optional

try:
    from dotenv import load_dotenv
    import vertexai
    from google.oauth2 import service_account
    from vertexai.generative_models import GenerativeModel
except ImportError as e:
    print(f"Missing required dependency: {e}")
    print("Please install: pip install google-cloud-aiplatform python-dotenv google-auth")
    raise ImportError(f"Missing dependencies: {e}")


class GeminiClient:
    """Client for Gemini generative AI model."""
    
    def __init__(self, config):
        """
        Initialize Gemini client.
        
        Args:
            config: Configuration object with Gemini settings
        """
        self.config = config
        self.model = None
        gemini_config = config.get("gemini", {})
        self.primary_model = gemini_config.get("model", "gemini-2.5-flash")
        self.fallback_model = "gemini-2.0-flash-exp"
        self.max_tokens = gemini_config.get("max_tokens", 4096)
        self.temperature = gemini_config.get("temperature", 0.1)
        self.current_model = None
        
    def _initialize_model(self, logger=None):
        """Initialize Gemini model with fallback logic."""
        if not self.model:
            # Import here to avoid circular imports
            from vertexai.generative_models import GenerativeModel
            import google.api_core.exceptions
            
            # Try primary model first
            try:
                if logger:
                    logger.log_info("GEMINI_INIT", f"Attempting to initialize Gemini model: {self.primary_model}")
                
                self.model = GenerativeModel(self.primary_model)
                self.current_model = self.primary_model
                
                if logger:
                    logger.log_info("GEMINI_INIT", f"Successfully initialized Gemini model: {self.current_model}")
                return
            except google.api_core.exceptions.NotFound as e:
                if logger:
                    logger.log_warning("GEMINI_INIT", f"Primary model {self.primary_model} not found", {"error": str(e)})
            except Exception as e:
                if logger:
                    logger.log_error("GEMINI_INIT", e, {"model": self.primary_model})
            
            # Fallback to secondary model
            try:
                if logger:
                    logger.log_info("GEMINI_INIT", f"Attempting fallback model: {self.fallback_model}")
                
                self.model = GenerativeModel(self.fallback_model)
                self.current_model = self.fallback_model
                
                if logger:
                    logger.log_info("GEMINI_INIT", f"Successfully initialized fallback Gemini model: {self.current_model}")
            except Exception as e:
                if logger:
                    logger.log_error("GEMINI_INIT", e, {"primary_model": self.primary_model, "fallback_model": self.fallback_model})
                raise Exception(f"Failed to initialize both Gemini models: {e}")
    
    def generate_answer(self, query_text: str, context: str, logger=None) -> Dict[str, Any]:
        """
        Generate answer using Gemini with provided context.
        
        Args:
            query_text: User's question
            context: Retrieved document context
            logger: Optional QueryLogger instance
            
        Returns:
            Dictionary with answer and metadata
        """
        self._initialize_model(logger)
        
        try:
            # Format prompt for Gemini
            if not context or "unavailable" in context.lower():
                prompt = f"""You are a FastAPI expert. The user asked: {query_text}

Unfortunately, I couldn't find relevant documentation to answer this question. Please provide a helpful general response about FastAPI based on your knowledge, but clearly indicate that you don't have access to specific documentation for this query."""
            else:
                prompt = f"""You are a FastAPI expert. Using ONLY the following documentation context, answer the user question. If the answer isn't in the context, say you don't know.

Context: {context}

Question: {query_text}"""
            
            if logger:
                logger.log_gemini_call_start(self.current_model, len(prompt))
                logger.log_info("GEMINI_PROMPT", f"Generated prompt for Gemini", {
                    "prompt": prompt,
                    "prompt_length": len(prompt),
                    "context_available": bool(context and "unavailable" not in context.lower())
                })
                if context:
                    logger.log_info("GEMINI_CONTEXT", f"Retrieved context for query", {
                        "context": context,
                        "context_length": len(context)
                    })
            
            # Generate response
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "max_output_tokens": self.max_tokens,
                    "temperature": self.temperature,
                }
            )
            
            answer = response.text
            sources = self._extract_sources(context)
            tokens_used = len(response.text.split()) if response.text else 0
            
            if logger:
                logger.log_info("GEMINI_RESPONSE", f"Generated response from Gemini", {
                    "response": answer,
                    "response_length": len(answer),
                    "tokens_used": tokens_used,
                    "sources_extracted": sources
                })
                logger.log_gemini_call_complete(self.current_model, len(answer), tokens_used)
            
            return {
                "answer": answer,
                "sources": sources,
                "model": self.current_model,
                "tokens_used": tokens_used
            }
            
        except Exception as e:
            if logger:
                logger.log_error("GEMINI_GENERATION", e, {"query_text": query_text, "context_length": len(context)})
            
            return {
                "answer": f"Sorry, I encountered an error: {str(e)}",
                "sources": [],
                "error": str(e)
            }
    
    def _extract_sources(self, context: str) -> List[str]:
        """
        Extract source information from context.
        
        Args:
            context: Formatted context string
            
        Returns:
            List of unique source URLs/paths
        """
        sources = []
        # Simple extraction - look for source patterns in context
        # This is a basic implementation - can be enhanced
        lines = context.split('\n')
        for line in lines:
            if 'source:' in line.lower():
                # Extract source path
                source = line.split('source:')[-1].strip()
                if source and source not in sources:
                    sources.append(source)
        
        return sources
