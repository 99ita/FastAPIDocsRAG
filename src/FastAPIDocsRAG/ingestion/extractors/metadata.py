"""
Metadata extraction utilities for MkDocs configuration.
"""

import yaml
import os
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class NavigationNode:
    """Represents a node in the documentation navigation structure."""
    title: str
    path: Optional[str]
    children: List['NavigationNode']
    parent: Optional['NavigationNode'] = None
    section: Optional[str] = None
    level: int = 0
    is_section: bool = False
    
    def get_full_path(self) -> str:
        """Get the full path from root to this node."""
        if self.parent is None:
            return self.title
        parent_path = self.parent.get_full_path()
        return f"{parent_path} > {self.title}"
    
    def get_depth(self) -> int:
        """Get the depth of this node in the navigation tree."""
        return self.level


class MkDocsMetadataExtractor:
    """Extract metadata from MkDocs configuration for RAG enhancement."""
    
    def __init__(self, mkdocs_path: str = "./mkdocs.yml"):
        """
        Initialize MkDocs metadata extractor.
        
        Args:
            mkdocs_path: Path to mkdocs.yml file
        """
        self.mkdocs_path = mkdocs_path
        self.navigation_tree = None
        self.section_mapping = {}
        self.path_to_node = {}
        self._parse_mkdocs()
    
    def _parse_mkdocs(self):
        """Parse only the navigation section from mkdocs.yml."""
        try:
            with open(self.mkdocs_path, 'r', encoding='utf-8') as f:
                mkdocs_config = yaml.safe_load(f)
            
            # Parse navigation structure only
            nav_items = mkdocs_config.get('nav', [])
            self.navigation_tree = self._build_navigation_tree(nav_items)
            
            # Build mappings for easy lookup
            self._build_mappings()
            
        except yaml.YAMLError as e:
            print(f"Warning: YAML parsing failed: {str(e)}")
            # Try to parse with a more permissive approach
            try:
                with open(self.mkdocs_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Remove problematic Python-specific tags
                    content = re.sub(r'!!python/name:[^\s]+', 'null', content)
                    mkdocs_config = yaml.safe_load(content)
                
                nav_items = mkdocs_config.get('nav', [])
                self.navigation_tree = self._build_navigation_tree(nav_items)
                self._build_mappings()
                
            except Exception as e2:
                print(f"Warning: Failed to parse mkdocs.yml even after cleanup: {str(e2)}")
                self.navigation_tree = NavigationNode("Root", None, [])
        except Exception as e:
            print(f"Warning: Failed to parse mkdocs.yml: {str(e)}")
            self.navigation_tree = NavigationNode("Root", None, [])
    
    def _build_navigation_tree(self, nav_items: List[Any], parent: Optional[NavigationNode] = None, level: int = 0) -> NavigationNode:
        """Build a tree structure from navigation items."""
        root = NavigationNode("Root", None, [], parent, level=level, is_section=True)
        
        for item in nav_items:
            if isinstance(item, str):
                # Simple string item - treat as a page with path
                node = NavigationNode(item, item, [], root, level=level + 1)
                root.children.append(node)
            elif isinstance(item, dict):
                # Dict with title and content
                for title, content in item.items():
                    if isinstance(content, list):
                        # Section with list of children
                        section_node = NavigationNode(title, None, [], root, level=level + 1, is_section=True)
                        root.children.append(section_node)
                        
                        # Process each item in the list
                        for child_item in content:
                            if isinstance(child_item, str):
                                # String item - create a page node
                                page_node = NavigationNode(child_item, child_item, [], section_node, level=level + 2)
                                section_node.children.append(page_node)
                            elif isinstance(child_item, dict):
                                # Nested dict - recurse
                                child_tree = self._build_navigation_tree([child_item], section_node, level + 2)
                                section_node.children.extend(child_tree.children)
                    elif isinstance(content, str):
                        # Leaf node with path
                        node = NavigationNode(title, content, [], root, level=level + 1)
                        root.children.append(node)
                    else:
                        # Handle None or other types as sections
                        section_node = NavigationNode(title, None, [], root, level=level + 1, is_section=True)
                        root.children.append(section_node)
        
        return root
    
    def _build_mappings(self):
        """Build lookup tables for navigation nodes and sections."""
        def traverse_tree(node: NavigationNode):
            # Map node to its path
            if node.path:
                self.path_to_node[node.path] = node
            
            # Map path to section
            if node.path and not node.is_section:
                section = self._get_parent_section(node)
                if section:
                    self.section_mapping[node.path] = section
            
            # Recursively process children
            for child in node.children:
                traverse_tree(child)
        
        traverse_tree(self.navigation_tree)
    
    def _get_parent_section(self, node: NavigationNode) -> Optional[str]:
        """Get the parent section for a node."""
        current = node.parent
        while current:
            if current.is_section and current.title != "Root":
                return current.title
            current = current.parent
        return None
    
    def get_metadata_for_file(self, file_path: str) -> Dict[str, Any]:
        """Get enhanced metadata for a specific file."""
        # Normalize file path - handle both Windows and Unix paths
        normalized_path = file_path
        
        # Remove leading ./docs/ or docs/ if present
        if normalized_path.startswith('./docs/'):
            normalized_path = normalized_path[7:]
        elif normalized_path.startswith('docs/'):
            normalized_path = normalized_path[5:]
        elif normalized_path.startswith('./docs\\'):
            normalized_path = normalized_path[7:].replace('\\', '/')
        elif normalized_path.startswith('docs\\'):
            normalized_path = normalized_path[5:].replace('\\', '/')
        
        # Convert all backslashes to forward slashes for consistency
        normalized_path = normalized_path.replace('\\', '/')
        
        # Remove leading slash if present
        if normalized_path.startswith('/'):
            normalized_path = normalized_path[1:]
        
        # Find the navigation node for this file
        node = self.path_to_node.get(normalized_path)
        if not node:
            return self._get_default_metadata()
        
        # Build metadata
        metadata = {
            'navigation_title': node.title,
            'navigation_path': node.get_full_path(),
            'navigation_depth': node.get_depth(),
            'section': self.section_mapping.get(normalized_path),
            'is_section': node.is_section,
            'parent_section': self._get_parent_section(node),
            'learning_level': self._determine_learning_level(node),
            'difficulty': self._determine_difficulty(node)
        }
        
        return metadata
    
    def _get_default_metadata(self) -> Dict[str, Any]:
        """Get default metadata for files not in navigation."""
        return {
            'navigation_title': '',
            'navigation_path': '',
            'navigation_depth': 0,
            'section': None,
            'is_section': False,
            'parent_section': None,
            'learning_level': 'unknown',
            'difficulty': 'unknown'
        }
    
    def _determine_learning_level(self, node: NavigationNode) -> str:
        """Determine learning level based on navigation context."""
        title = node.title.lower()
        path = node.get_full_path().lower()
        
        if any(keyword in title or keyword in path for keyword in ['tutorial', 'first steps', 'beginner', 'intro']):
            return 'beginner'
        elif any(keyword in title or keyword in path for keyword in ['advanced', 'expert', 'deep']):
            return 'advanced'
        elif any(keyword in title or keyword in path for keyword in ['how to', 'recipe', 'guide']):
            return 'intermediate'
        else:
            return 'intermediate'
    
    def _determine_difficulty(self, node: NavigationNode) -> str:
        """Determine difficulty based on navigation context."""
        level = self._determine_learning_level(node)
        if level == 'beginner':
            return 'beginner'
        elif level == 'advanced':
            return 'advanced'
        else:
            return 'intermediate'


# Global instance for convenience
_mkdocs_parser_instance = None


def get_mkdocs_parser(mkdocs_path: str = "./mkdocs.yml") -> MkDocsMetadataExtractor:
    """Get or create a MkDocs parser instance."""
    global _mkdocs_parser_instance
    if _mkdocs_parser_instance is None or _mkdocs_parser_instance.mkdocs_path != mkdocs_path:
        _mkdocs_parser_instance = MkDocsMetadataExtractor(mkdocs_path)
    return _mkdocs_parser_instance
