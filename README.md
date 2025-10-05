# Terraform Graph to Neo4j Ingestion [POC]

This project automates the ingestion of Terraform's dependency graph into a Neo4j database for analysis and visualization. It also provides a pattern for using the ingested graph as structured context for an AI agent via a Model-Context-Protocol (MCP).

## Project goal: Neo4j as context for an AI agent (MCP)

The primary purpose of this project is to store and visualize Terraform's dependency graph and to turn that information into usable context for an AI agent.

- The topology of resources, metadata and relationships in Neo4j can be exposed as structured context that an AI agent queries to make decisions, reason about infrastructure changes, generate explanations, or propose actions.
- Typical use case: an AI agent receives a request (for example "what would happen if I remove this resource?"), queries Neo4j for the relevant subgraph, and uses that subgraph as context to generate a response or feed an automated analysis pipeline.

### Minimal contract (inputs / outputs)

- System input: resource identifier(s) or natural language queries from the AI agent.
- System output: serialized subgraph (nodes and relationships) as JSON and/or Cypher query results.
- Errors: inability to connect to Neo4j, invalid credentials, empty graph, or invalid queries.

### Recommended data flow

1. Generate and parse the Terraform graph (file `graph.json`).
2. Ingest nodes and relations into Neo4j using `neo4j_connector.py`.
3. A MCP component runs Cypher queries to extract relevant subgraphs.
4. Transform the subgraph into a compact representation (JSON with nodes/edges and properties) and pass it to the model as context.
5. The agent returns an answer and optionally performs actions (e.g., open a ticket, apply Terraform changes).

### Example Cypher query useful for an MCP

Extract dependency subgraph up to N hops from a given resource:

```cypher
MATCH (r:TerraformResource {id: $resource_id})
MATCH path = (r)-[:DEPENDS_ON*0..$depth]->(m)
RETURN nodes(path) AS nodes, relationships(path) AS edges
```

Parameters:

- `$resource_id`: id of the root resource
- `$depth`: maximum number of hops to explore

The MCP can execute this query and serialize `nodes` and `edges` to JSON for the AI model.

### Recommendations to integrate with an MCP

- Normalize serialization: include `id`, `label`, `name` and relevant properties.
- Filter sensitive properties (passwords, secrets) before sending context to the model.
- Implement size limits and summarization to avoid overloading model prompts.
- Use indexes and constraints in Neo4j to speed up MCP queries (see `create_constraints()` in `neo4j_connector.py`).

### Minimal integration example

1. Ingest the graph with the main script:

```bash
python main.py
```

2. From your agent/MCP, connect to Neo4j (use the same `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`) and run the subgraph query shown above.

3. Serialize the returned nodes/edges and attach them to the model prompt/context (for example, as a JSON field named `graph_context`).

4. The agent generates the response and, if appropriate, returns a structured action or recommendation.

### Example integration snippet (Python)

This minimal snippet shows how an MCP component could query Neo4j and serialize the subgraph for a model. It intentionally omits robust error handling and secure credential management—adapt it for production.

```python
from neo4j import GraphDatabase
import json

NEO4J_URI = 'bolt://localhost:7687'
NEO4J_USER = 'neo4j'
NEO4J_PASSWORD = 'your_password'

CYPHER_SUBGRAPH = '''
MATCH (r:TerraformResource {id: $resource_id})
MATCH path = (r)-[:DEPENDS_ON*0..$depth]->(m)
RETURN nodes(path) AS nodes, relationships(path) AS edges
'''

def get_subgraph(resource_id: str, depth: int = 2):
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        result = session.run(CYPHER_SUBGRAPH, resource_id=resource_id, depth=depth)
        record = result.single()
        nodes = record['nodes']
        edges = record['edges']

    # Map nodes and relationships to JSON-serializable structures
    serial_nodes = []
    for n in nodes:
        serial_nodes.append({
            'id': n.get('id'),
            'labels': list(n.labels),
            'properties': dict(n.items())
        })

    serial_edges = []
    for e in edges:
        serial_edges.append({
            'source': e.start_node.get('id'),
            'target': e.end_node.get('id'),
            'type': e.type,
            'properties': dict(e.items())
        })

    return json.dumps({'nodes': serial_nodes, 'edges': serial_edges})
```

> Note: adapt the snippet for your Neo4j driver version and include proper error handling and credential management.

---

## Prerequisites

- Python 3.8 or higher
- Terraform installed ([terraform downloads](https://www.terraform.io/downloads))
- Graphviz installed (for the `dot` command) ([graphviz downloads](https://graphviz.org/download/))
- Neo4j database (local or remote) ([neo4j downloads](https://neo4j.com/download/))

### Installation

```bash
cd terraform-context
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` with your Neo4j credentials:

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
```

### Usage

Generate and ingest the graph (run this in a Terraform configuration directory):

```bash
python main.py
```

Advanced options:

```bash
python main.py --graph-file my_graph.json --skip-generate
python main.py --no-clear
python main.py --help
```

## Project Structure

```
terraform-context/
├── main.py
├── graph_parser.py
├── neo4j_connector.py
├── requirements.txt
├── .env.example
├── .env  # not versioned
└── README.md
```

## License

This project is open source and available under the MIT license.
