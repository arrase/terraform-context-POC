# Quick Start

## 5-Minute Setup

### 1. Install Neo4j with Docker (fastest option)

```bash
docker run \
    --name neo4j \
    -p 7474:7474 -p 7687:7687 \
    -e NEO4J_AUTH=neo4j/password123 \
    -d neo4j:community
```

Access Neo4j Browser at: http://localhost:7474
- Username: `neo4j`
- Password: `neo4j`

### 2. Configure the project

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
```

Edit `.env`:
```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password123
```

### 3. Test with the included example

```bash
# Initialize Terraform with the example
terraform init

# Run the ingestion
python main.py
```

### 4. Visualize in Neo4j Browser

Open http://localhost:7474 and run:

```cypher
MATCH (n)-[r]->(m)
RETURN n, r, m
```

## Use with your own Terraform project

```bash
# Navigate to your Terraform directory
cd /path/to/your/terraform/project

# Run the script (adjust the path)
python /path/to/terraform-context/main.py
```

## Useful commands

### View statistics in Neo4j
```cypher
MATCH (n:TerraformResource)
OPTIONAL MATCH ()-[r:DEPENDS_ON]->()
RETURN count(DISTINCT n) AS nodes, count(r) AS relationships
```

### Find resources without dependencies
```cypher
MATCH (n:TerraformResource)
WHERE NOT (n)-[:DEPENDS_ON]->()
AND NOT ()-[:DEPENDS_ON]->(n)
RETURN n
```

### View root resources (entry point)
```cypher
MATCH (n:TerraformResource)
WHERE NOT ()-[:DEPENDS_ON]->(n)
RETURN n
```

### Find longest dependency chains
```cypher
MATCH path = (start)-[:DEPENDS_ON*]->(end)
WHERE NOT ()-[:DEPENDS_ON]->(start)
  AND NOT (end)-[:DEPENDS_ON]->()
RETURN path
ORDER BY length(path) DESC
LIMIT 5
```

## Quick troubleshooting

**Error: "terraform command not found"**
```bash
# Ubuntu/Debian
sudo apt-get install terraform

# macOS
brew install terraform
```

**Error: "dot command not found"**
```bash
# Ubuntu/Debian
sudo apt-get install graphviz

# macOS
brew install graphviz
```

**Error: "Failed to connect to Neo4j"**
- Verify the container is running: `docker ps | grep neo4j`
- Restart Neo4j: `docker restart neo4j`
- Check credentials in `.env`
