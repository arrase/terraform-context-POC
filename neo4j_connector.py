"""
Neo4j connector module for ingesting Terraform graph data.
"""

from neo4j import GraphDatabase
from typing import List, Dict, Any
import os


class Neo4jConnector:
    """Handles connection and data ingestion to Neo4j database."""
    
    def __init__(self, uri: str, user: str, password: str):
        """
        Initialize Neo4j connection.
        
        Args:
            uri: Neo4j connection URI (e.g., bolt://localhost:7687)
            user: Neo4j username
            password: Neo4j password
        """
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None
    
    def connect(self) -> None:
        """Establish connection to Neo4j database."""
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            # Verify connectivity
            self.driver.verify_connectivity()
            print(f"✓ Connected to Neo4j at {self.uri}")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Neo4j: {e}")
    
    def close(self) -> None:
        """Close the Neo4j driver connection."""
        if self.driver:
            self.driver.close()
            print("✓ Neo4j connection closed")
    
    def clear_database(self) -> None:
        """Clear all nodes and relationships from the database."""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            print("✓ Database cleared")
    
    def create_constraints(self) -> None:
        """Create uniqueness constraints for node IDs."""
        with self.driver.session() as session:
            # Create constraint for TerraformResource nodes
            try:
                session.run("""
                    CREATE CONSTRAINT terraform_resource_id IF NOT EXISTS
                    FOR (n:TerraformResource) REQUIRE n.id IS UNIQUE
                """)
                print("✓ Created constraint for TerraformResource nodes")
            except Exception as e:
                print(f"Note: Constraint may already exist: {e}")
    
    def ingest_nodes(self, nodes: List[Dict[str, Any]]) -> int:
        """
        Ingest nodes into Neo4j.
        
        Args:
            nodes: List of node dictionaries
            
        Returns:
            Number of nodes created
        """
        if not nodes:
            print("⚠ No nodes to ingest")
            return 0
        
        with self.driver.session() as session:
            result = session.run("""
                UNWIND $nodes AS node
                MERGE (n:TerraformResource {id: node.id})
                SET n += node
                RETURN count(n) AS count
            """, nodes=nodes)
            
            count = result.single()['count']
            print(f"✓ Ingested {count} nodes")
            return count
    
    def ingest_edges(self, edges: List[Dict[str, Any]]) -> int:
        """
        Ingest edges/relationships into Neo4j.
        
        Args:
            edges: List of edge dictionaries with source, target, and label
            
        Returns:
            Number of relationships created
        """
        if not edges:
            print("⚠ No edges to ingest")
            return 0
        
        with self.driver.session() as session:
            result = session.run("""
                UNWIND $edges AS edge
                MATCH (source:TerraformResource {id: edge.source})
                MATCH (target:TerraformResource {id: edge.target})
                MERGE (source)-[r:DEPENDS_ON]->(target)
                SET r.label = edge.label
                RETURN count(r) AS count
            """, edges=edges)
            
            count = result.single()['count']
            print(f"✓ Ingested {count} relationships")
            return count
    
    def ingest_graph(self, graph_data: Dict[str, Any], clear_existing: bool = True) -> Dict[str, int]:
        """
        Ingest complete graph data into Neo4j.
        
        Args:
            graph_data: Dictionary with 'nodes', 'edges', and 'metadata' keys
            clear_existing: Whether to clear existing data before ingesting
            
        Returns:
            Dictionary with counts of nodes and edges created
        """
        if clear_existing:
            self.clear_database()
        
        self.create_constraints()
        
        nodes_count = self.ingest_nodes(graph_data.get('nodes', []))
        edges_count = self.ingest_edges(graph_data.get('edges', []))
        
        metadata = graph_data.get('metadata', {})
        print(f"\n✓ Graph ingestion complete!")
        print(f"  - Graph name: {metadata.get('name', 'N/A')}")
        print(f"  - Nodes created: {nodes_count}")
        print(f"  - Relationships created: {edges_count}")
        
        return {
            'nodes': nodes_count,
            'edges': edges_count
        }
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get database statistics.
        
        Returns:
            Dictionary with node and relationship counts
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (n:TerraformResource)
                OPTIONAL MATCH ()-[r:DEPENDS_ON]->()
                RETURN count(DISTINCT n) AS nodes, count(r) AS relationships
            """)
            
            record = result.single()
            return {
                'nodes': record['nodes'],
                'relationships': record['relationships']
            }
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
