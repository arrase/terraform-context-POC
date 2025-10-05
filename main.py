#!/usr/bin/env python3
"""
Main script to ingest Terraform graph into Neo4j.

Usage:
    python main.py [--graph-file GRAPH_FILE] [--clear] [--skip-generate]

Examples:
    # Generate graph and ingest into Neo4j
    python main.py
    
    # Use existing graph file
    python main.py --graph-file custom_graph.json --skip-generate
    
    # Don't clear existing data
    python main.py --no-clear
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
from dotenv import load_dotenv

from graph_parser import TerraformGraphParser
from neo4j_connector import Neo4jConnector


def generate_terraform_graph(output_file: str) -> bool:
    """
    Generate Terraform graph using terraform and dot commands.
    
    Args:
        output_file: Path to save the graph JSON file
        
    Returns:
        True if successful, False otherwise
    """
    print("\n🔄 Generating Terraform graph...")
    
    try:
        # Check if terraform is available
        subprocess.run(['terraform', 'version'], 
                      capture_output=True, 
                      check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Error: terraform command not found. Please install Terraform.")
        return False
    
    try:
        # Check if dot (graphviz) is available
        subprocess.run(['dot', '-V'], 
                      capture_output=True, 
                      check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Error: dot command not found. Please install Graphviz.")
        return False
    
    try:
        # Generate the graph: terraform graph | dot -Tjson > graph.json
        terraform_proc = subprocess.Popen(
            ['terraform', 'graph'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        with open(output_file, 'w') as f:
            dot_proc = subprocess.run(
                ['dot', '-Tjson'],
                stdin=terraform_proc.stdout,
                stdout=f,
                stderr=subprocess.PIPE,
                check=True
            )
        
        terraform_proc.wait()
        
        if terraform_proc.returncode != 0:
            stderr = terraform_proc.stderr.read().decode()
            print(f"❌ Terraform graph generation failed: {stderr}")
            return False
        
        print(f"✓ Graph generated successfully: {output_file}")
        return True
        
    except Exception as e:
        print(f"❌ Error generating graph: {e}")
        return False


def main():
    """Main execution function."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Ingest Terraform graph into Neo4j database'
    )
    parser.add_argument(
        '--graph-file',
        default='graph.json',
        help='Path to graph JSON file (default: graph.json)'
    )
    parser.add_argument(
        '--skip-generate',
        action='store_true',
        help='Skip terraform graph generation and use existing file'
    )
    parser.add_argument(
        '--no-clear',
        action='store_true',
        help='Do not clear existing data in Neo4j before ingesting'
    )
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Get Neo4j configuration
    neo4j_uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
    neo4j_user = os.getenv('NEO4J_USER', 'neo4j')
    neo4j_password = os.getenv('NEO4J_PASSWORD')
    
    if not neo4j_password:
        print("❌ Error: NEO4J_PASSWORD not set in environment variables")
        print("Please create a .env file based on .env.example")
        sys.exit(1)
    
    # Generate graph if needed
    if not args.skip_generate:
        if not generate_terraform_graph(args.graph_file):
            sys.exit(1)
    
    # Check if graph file exists
    if not Path(args.graph_file).exists():
        print(f"❌ Error: Graph file not found: {args.graph_file}")
        sys.exit(1)
    
    try:
        # Parse the graph
        print(f"\n📊 Parsing graph from {args.graph_file}...")
        parser = TerraformGraphParser(args.graph_file)
        graph_data = parser.parse()
        
        # Connect to Neo4j and ingest data
        print(f"\n🔌 Connecting to Neo4j at {neo4j_uri}...")
        with Neo4jConnector(neo4j_uri, neo4j_user, neo4j_password) as connector:
            clear_existing = not args.no_clear
            connector.ingest_graph(graph_data, clear_existing=clear_existing)
            
            # Display final stats
            stats = connector.get_stats()
            print(f"\n📈 Database statistics:")
            print(f"  - Total nodes: {stats['nodes']}")
            print(f"  - Total relationships: {stats['relationships']}")
        
        print("\n✅ Success! Terraform graph has been ingested into Neo4j")
        print(f"\nYou can now query your graph at {neo4j_uri}")
        print("Example query: MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 25")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
