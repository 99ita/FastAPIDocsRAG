"""
Logging utilities for FastAPI Documentation RAG system.
"""

import json
import time
import traceback
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from contextlib import contextmanager


class QueryLogger:
    """Logger for individual RAG query requests with timestamp-based files."""
    
    def __init__(self, log_dir: str = "./output/logs", query_id: Optional[str] = None):
        """
        Initialize query logger.
        
        Args:
            log_dir: Directory to store log files
            query_id: Optional query identifier (uses timestamp if not provided)
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate timestamp-based filename
        if query_id is None:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            query_id = timestamp
        
        self.log_file = self.log_dir / f"query-{query_id}.log"
        self.start_time = time.time()
        
        # Write initial log entry
        self._write_log("INIT", f"Query logging started for query {query_id}")
    
    def _write_log(self, stage: str, message: str, data: Optional[Dict[str, Any]] = None):
        """
        Write a log entry to the file and terminal.
        
        Args:
            stage: Processing stage identifier
            message: Log message
            data: Optional additional data to include
        """
        timestamp = datetime.now().isoformat()
        elapsed = time.time() - self.start_time
        
        log_entry = {
            "timestamp": timestamp,
            "elapsed_seconds": round(elapsed, 3),
            "stage": stage,
            "message": message
        }
        
        if data:
            log_entry["data"] = data
        
        # Format for terminal output
        terminal_msg = f"[{timestamp}] [{stage}] {message}"
        if data:
            terminal_msg += f" | Data: {json.dumps(data, default=str)}"
        
        # Always write to terminal
        print(terminal_msg, file=sys.stdout)
        
        # Also write to file
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, default=str) + '\n')
        except Exception as e:
            # Fallback to console if file writing fails
            print(f"Failed to write to log file {self.log_file}: {e}", file=sys.stderr)
            print(f"Log entry: {log_entry}", file=sys.stderr)
    
    def log_request_start(self, query: str, top_n: int, request_data: Optional[Dict] = None):
        """Log the start of a query request."""
        self._write_log("REQUEST_START", f"Processing query: {query[:100]}...", {
            "query": query,
            "top_n": top_n,
            "request_data": request_data
        })
    
    def log_vector_search_start(self, query_text: str):
        """Log the start of vector search."""
        self._write_log("VECTOR_SEARCH_START", f"Starting vector search for query: {query_text[:100]}...")
    
    def log_embedding_generation(self, query_text: str, embedding_dim: Optional[int] = None):
        """Log embedding generation."""
        self._write_log("EMBEDDING_GENERATION", f"Generated embedding for query", {
            "query_length": len(query_text),
            "embedding_dimensions": embedding_dim
        })
    
    def log_document_retrieval(self, num_docs: int, docs: Optional[list] = None):
        """Log document retrieval results."""
        self._write_log("DOCUMENT_RETRIEVAL", f"Retrieved {num_docs} similar documents", {
            "num_documents": num_docs,
            "document_ids": [doc.get("id", "unknown") for doc in docs] if docs else []
        })
    
    def log_context_assembly(self, context_length: int, sources: list):
        """Log context assembly."""
        self._write_log("CONTEXT_ASSEMBLY", f"Assembled context from {len(sources)} sources", {
            "context_length": context_length,
            "sources": sources
        })
    
    def log_gemini_call_start(self, model: str, prompt_length: int):
        """Log the start of Gemini API call."""
        self._write_log("GEMINI_CALL_START", f"Calling Gemini model: {model}", {
            "model": model,
            "prompt_length": prompt_length
        })
    
    def log_gemini_call_complete(self, model: str, response_length: int, tokens_used: int):
        """Log completion of Gemini API call."""
        self._write_log("GEMINI_CALL_COMPLETE", f"Gemini call completed successfully", {
            "model": model,
            "response_length": response_length,
            "tokens_used": tokens_used
        })
    
    def log_response_generation(self, answer_length: int, total_time: float):
        """Log final response generation."""
        self._write_log("RESPONSE_GENERATION", f"Generated final response", {
            "answer_length": answer_length,
            "total_processing_time": total_time
        })
    
    def log_request_complete(self, final_response: Dict[str, Any]):
        """Log completion of the entire request."""
        elapsed = time.time() - self.start_time
        self._write_log("REQUEST_COMPLETE", f"Query processing completed in {elapsed:.3f}s", {
            "total_time": elapsed,
            "response_summary": {
                "answer_length": len(final_response.get("answer", "")),
                "documents_retrieved": final_response.get("documents_retrieved", 0),
                "context_length": final_response.get("context_length", 0),
                "tokens_used": final_response.get("tokens_used", 0),
                "model": final_response.get("model", "")
            }
        })
    
    def log_error(self, stage: str, error: Exception, context: Optional[Dict] = None):
        """Log an error that occurred during processing."""
        self._write_log("ERROR", f"Error in {stage}: {str(error)}", {
            "stage": stage,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
            "context": context
        })
    
    def log_warning(self, stage: str, message: str, context: Optional[Dict] = None):
        """Log a warning message."""
        self._write_log("WARNING", message, {
            "stage": stage,
            "context": context
        })
    
    def log_info(self, stage: str, message: str, data: Optional[Dict] = None):
        """Log an informational message."""
        self._write_log("INFO", message, data)
    
    @contextmanager
    def timer(self, stage: str, description: str):
        """
        Context manager for timing operations.
        
        Args:
            stage: Processing stage identifier
            description: Description of the operation
        """
        start_time = time.time()
        self._write_log(f"{stage}_START", description)
        try:
            yield
            elapsed = time.time() - start_time
            self._write_log(f"{stage}_COMPLETE", f"{description} completed in {elapsed:.3f}s", {
                "duration_seconds": elapsed
            })
        except Exception as e:
            elapsed = time.time() - start_time
            self._write_log(f"{stage}_ERROR", f"{description} failed after {elapsed:.3f}s", {
                "duration_seconds": elapsed,
                "error": str(e)
            })
            raise
    
    def get_log_file_path(self) -> str:
        """Get the path to the log file."""
        return str(self.log_file)
    
    def close(self):
        """Close the logger and write final entry."""
        elapsed = time.time() - self.start_time
        self._write_log("CLOSE", f"Logger closed after {elapsed:.3f}s")


def create_query_logger(log_dir: str = "./output/logs", query_id: Optional[str] = None) -> QueryLogger:
    """
    Factory function to create a query logger.
    
    Args:
        log_dir: Directory to store log files
        query_id: Optional query identifier
        
    Returns:
        QueryLogger instance
    """
    return QueryLogger(log_dir=log_dir, query_id=query_id)
