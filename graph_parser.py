"""
Parser module for Terraform graph JSON files.
Processes the graph output from 'terraform graph | dot -Tjson' command.
"""

import json
from typing import Dict, List, Any


class TerraformGraphParser:
    """Parses Terraform graph JSON and extracts nodes and edges."""
    
    def __init__(self, file_path: str):
        """
        Initialize the parser with a graph file path.
        
        Args:
            file_path: Path to the graph.json file
        """
        self.file_path = file_path
        self.raw_data = None
        self.nodes = []
        self.edges = []
    
    def load_graph(self) -> None:
        """Load and parse the graph JSON file."""
        try:
            with open(self.file_path, 'r') as f:
                self.raw_data = json.load(f)
            print(f"✓ Graph file loaded successfully from {self.file_path}")
        except FileNotFoundError:
            raise FileNotFoundError(f"Graph file not found: {self.file_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in graph file: {e}")
    
    def parse_nodes(self) -> List[Dict[str, Any]]:
        """
        Extract and parse nodes from the graph.
        
        Returns:
            List of node dictionaries with properties
        """
        if not self.raw_data:
            raise ValueError("Graph data not loaded. Call load_graph() first.")
        
        self.nodes = []
        
        # The graph structure from 'dot -Tjson' has 'objects' array
        for obj in self.raw_data.get('objects', []):
            # Skip if not a node
            if obj.get('_gvid') is None:
                continue
            
            node = {
                'id': str(obj.get('_gvid')),
                'name': obj.get('name', ''),
                'label': obj.get('label', obj.get('name', '')),
            }
            
            # Add any additional attributes
            for key, value in obj.items():
                if key not in ['_gvid', 'name', 'label', '_draw_', '_ldraw_']:
                    node[key] = value
            
            self.nodes.append(node)
        
        print(f"✓ Parsed {len(self.nodes)} nodes")
        return self.nodes
    
    def parse_edges(self) -> List[Dict[str, Any]]:
        """
        Extract and parse edges from the graph.
        
        Returns:
            List of edge dictionaries with source, target, and properties
        """
        if not self.raw_data:
            raise ValueError("Graph data not loaded. Call load_graph() first.")
        
        self.edges = []
        
        # The graph structure from 'dot -Tjson' has 'edges' array
        for edge_data in self.raw_data.get('edges', []):
            edge = {
                'source': str(edge_data.get('tail')),
                'target': str(edge_data.get('head')),
                'label': edge_data.get('label', 'DEPENDS_ON'),
            }
            
            # Add any additional attributes
            for key, value in edge_data.items():
                if key not in ['tail', 'head', 'label', '_draw_', '_ldraw_', '_hdraw_']:
                    edge[key] = value
            
            self.edges.append(edge)
        
        print(f"✓ Parsed {len(self.edges)} edges")
        return self.edges
    
    def get_graph_metadata(self) -> Dict[str, Any]:
        """
        Extract metadata from the graph.
        
        Returns:
            Dictionary with graph metadata
        """
        if not self.raw_data:
            raise ValueError("Graph data not loaded. Call load_graph() first.")
        
        metadata = {
            'name': self.raw_data.get('name', 'terraform_graph'),
            'directed': self.raw_data.get('directed', True),
            'strict': self.raw_data.get('strict', False),
            'node_count': len(self.nodes),
            'edge_count': len(self.edges),
        }
        
        return metadata
    
    def parse(self) -> Dict[str, Any]:
        """
        Load and parse the entire graph.
        
        Returns:
            Dictionary with nodes, edges, and metadata
        """
        self.load_graph()
        nodes = self.parse_nodes()
        edges = self.parse_edges()
        metadata = self.get_graph_metadata()
        
        return {
            'nodes': nodes,
            'edges': edges,
            'metadata': metadata
        }
