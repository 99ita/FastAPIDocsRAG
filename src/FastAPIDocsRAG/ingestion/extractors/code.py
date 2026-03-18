"""
Code reference extraction utilities.
"""

import os
import re
from typing import Dict, List, Tuple, Any, Optional


class CodeExtractor:
    """Extract code snippets from documentation references."""
    
    def __init__(self, docs_src_path: str = "./docs_src"):
        """
        Initialize code extractor.
        
        Args:
            docs_src_path: Path to source code directory
        """
        self.docs_src_path = docs_src_path
        self.code_cache: Dict[str, Dict[str, Any]] = {}
        
        # Regex pattern for code references: {* path/file.py ln[lines] hl[lines] *} or {* path/file.py hl[lines] *}
        self.reference_pattern = re.compile(r'\{\*\s*([^}]+?)\s+(?:ln\[[^\]]+\]\s+)?hl\[([^\]]+)\]\s*\*\}')
    
    def extract_code_from_reference(self, reference: str) -> Tuple[str, Dict[str, Any]]:
        """
        Extract code content from a reference like '{* ../../docs_src/extra_models/tutorial005_py310.py hl[6] *}'
        
        Args:
            reference: Code reference string
            
        Returns:
            Tuple of (extracted_code, metadata)
        """
        # Parse the reference
        parsed = self._parse_reference(reference)
        if not parsed:
            return reference, {"error": "Failed to parse reference"}
        
        file_path = parsed["file_path"]
        line_ranges = parsed["line_ranges"]
        
        # Normalize the file path - remove leading ../../docs_src/ if present
        original_path = file_path
        if file_path.startswith("'") and file_path.endswith("'"):
            file_path = file_path[1:-1]  # Remove surrounding quotes first
        
        if file_path.startswith("../../docs_src/"):
            file_path = file_path[14:]  # Remove "../../docs_src/"
        elif file_path.startswith("../"):
            # Handle other relative paths
            file_path = file_path[3:]  # Remove leading "../"
        
        # Remove leading slash if present
        if file_path.startswith("/"):
            file_path = file_path[1:]  # Remove leading "/"
        
        # Check cache first
        cache_key = f"{file_path}:{str(line_ranges)}"
        if cache_key in self.code_cache:
            return self.code_cache[cache_key]["code"], self.code_cache[cache_key]["metadata"]
        
        # Extract the code
        try:
            full_path = os.path.join(self.docs_src_path, file_path)
            if not os.path.exists(full_path):
                return reference, {"error": f"File not found: {full_path}"}
            
            with open(full_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            extracted_lines = []
            for start, end in line_ranges:
                # Adjust for 0-based indexing and validate ranges
                start_idx = max(0, start - 1)
                end_idx = min(len(lines), end)
                
                for i in range(start_idx, end_idx):
                    if i < len(lines):
                        extracted_lines.append(lines[i].rstrip())
            
            code_content = '\n'.join(extracted_lines)
            
            # Format as code block
            formatted_code = f"```python\n{code_content}\n```"
            
            metadata = {
                "source_file": file_path,
                "line_ranges": line_ranges,
                "extracted_lines": len(extracted_lines),
                "reference": reference
            }
            
            # Cache the result
            self.code_cache[cache_key] = {
                "code": formatted_code,
                "metadata": metadata
            }
            
            return formatted_code, metadata
            
        except Exception as e:
            return reference, {"error": f"Extraction failed: {str(e)}"}
    
    def _parse_reference(self, reference: str) -> Optional[Dict[str, Any]]:
        """Parse a code reference string."""
        match = self.reference_pattern.match(reference)
        if not match:
            return None
        
        file_path = match.group(1).strip()
        lines_spec = match.group(2).strip()
        
        # Parse line ranges
        line_ranges = []
        for part in lines_spec.split(','):
            part = part.strip()
            if ':' in part:
                # Range like "14:15"
                start, end = map(int, part.split(':'))
                line_ranges.append((start, end))
            else:
                # Single line like "6"
                line = int(part)
                line_ranges.append((line, line + 1))
        
        return {
            "file_path": file_path,
            "line_ranges": line_ranges
        }
    
    def process_code_references(self, text: str) -> str:
        """
        Process all code references in text and replace with extracted code.
        
        Args:
            text: Text containing code references
            
        Returns:
            Text with code references replaced by extracted code
        """
        def replace_reference(match):
            reference = match.group(0)
            extracted_code, metadata = self.extract_code_from_reference(reference)
            
            if "error" in metadata:
                print(f"Warning: {metadata['error']} - Reference: {reference}")
                return reference
            
            return extracted_code
        
        return self.reference_pattern.sub(replace_reference, text)


# Global instance for convenience
_code_extractor_instance = None


def get_code_extractor(docs_src_path: str = "./docs_src") -> CodeExtractor:
    """Get or create a code extractor instance."""
    global _code_extractor_instance
    if _code_extractor_instance is None or _code_extractor_instance.docs_src_path != docs_src_path:
        _code_extractor_instance = CodeExtractor(docs_src_path)
    return _code_extractor_instance
