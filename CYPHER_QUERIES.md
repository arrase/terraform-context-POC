# Useful Cypher Queries for Terraform Graph

This document contains useful Cypher queries to analyze the Terraform graph in Neo4j.

## Basic Queries

### View all resources (limited)
```cypher
MATCH (n:TerraformResource)
RETURN n
LIMIT 25
```

### View all dependencies
```cypher
MATCH (source)-[r:DEPENDS_ON]->(target)
RETURN source, r, target
LIMIT 50
```

### Count resources and dependencies
```cypher
MATCH (n:TerraformResource)
OPTIONAL MATCH ()-[r:DEPENDS_ON]->()
RETURN count(DISTINCT n) AS total_resources, count(r) AS total_dependencies
```

## Dependency Analysis

### Resources without any dependencies (isolated)
```cypher
MATCH (n:TerraformResource)
WHERE NOT (n)-[:DEPENDS_ON]->() 
  AND NOT ()-[:DEPENDS_ON]->(n)
RETURN n.name AS isolated_resource, n.label AS label
```

### Root resources (graph entry)
```cypher
MATCH (n:TerraformResource)
WHERE NOT ()-[:DEPENDS_ON]->(n)
  AND (n)-[:DEPENDS_ON]->()
RETURN n.name AS root_resource, n.label AS label
ORDER BY n.name
```

### Leaf resources (graph exit)
```cypher
MATCH (n:TerraformResource)
WHERE NOT (n)-[:DEPENDS_ON]->()
  AND ()-[:DEPENDS_ON]->(n)
RETURN n.name AS leaf_resource, n.label AS label
ORDER BY n.name
```

### Resources with most outgoing dependencies
```cypher
MATCH (n:TerraformResource)-[r:DEPENDS_ON]->()
RETURN n.name AS resource, n.label AS label, count(r) AS dependencies_count
ORDER BY dependencies_count DESC
LIMIT 10
```

### Resources with most incoming dependencies
```cypher
MATCH ()-[r:DEPENDS_ON]->(n:TerraformResource)
RETURN n.name AS resource, n.label AS label, count(r) AS dependents_count
ORDER BY dependents_count DESC
LIMIT 10
```

## Path Analysis

### Longest dependency paths
```cypher
MATCH path = (start:TerraformResource)-[:DEPENDS_ON*]->(end:TerraformResource)
WHERE NOT ()-[:DEPENDS_ON]->(start)
  AND NOT (end)-[:DEPENDS_ON]->()
RETURN path, length(path) AS path_length
ORDER BY path_length DESC
LIMIT 5
```

### All dependencies of a specific resource
```cypher
MATCH path = (n:TerraformResource {name: 'resource_name'})-[:DEPENDS_ON*]->(dependency)
RETURN path
```

### All resources that depend on a specific one
```cypher
MATCH path = (dependent)-[:DEPENDS_ON*]->(n:TerraformResource {name: 'resource_name'})
RETURN path
```

### Distance between two resources
```cypher
MATCH path = shortestPath(
  (a:TerraformResource {name: 'resource_a'})-[:DEPENDS_ON*]-(b:TerraformResource {name: 'resource_b'})
)
RETURN path, length(path) AS distance
```

## Problem Detection

### Detect circular dependencies
```cypher
MATCH (n:TerraformResource)-[:DEPENDS_ON*]->(n)
RETURN DISTINCT n.name AS resource_in_cycle, n.label AS label
```

### Resources with circular dependencies (complete path)
```cypher
MATCH path = (n:TerraformResource)-[:DEPENDS_ON*]->(n)
RETURN path
LIMIT 10
```

### Orphan resources (possible configuration issues)
```cypher
MATCH (n:TerraformResource)
WHERE NOT (n)-[:DEPENDS_ON]->() 
  AND NOT ()-[:DEPENDS_ON]->(n)
  AND n.name IS NOT NULL
RETURN n.name AS orphan_resource, n.label AS label
```

## Analysis by Resource Type

### Count resources by type (using name prefix)
```cypher
MATCH (n:TerraformResource)
WITH n, split(n.name, '.')[0] AS resource_type
RETURN resource_type, count(n) AS count
ORDER BY count DESC
```

### List all unique resource types
```cypher
MATCH (n:TerraformResource)
WITH DISTINCT split(n.name, '.')[0] AS resource_type
RETURN collect(resource_type) AS resource_types
```

### Resources of a specific type
```cypher
MATCH (n:TerraformResource)
WHERE n.name STARTS WITH 'aws_instance'
RETURN n.name AS instance, n.label AS label
ORDER BY n.name
```

## Visualization

### Complete graph (use with caution on large graphs)
```cypher
MATCH (n:TerraformResource)
OPTIONAL MATCH (n)-[r:DEPENDS_ON]->(m)
RETURN n, r, m
```

### Subgraph from a resource (2 levels)
```cypher
MATCH path = (n:TerraformResource {name: 'resource_name'})-[:DEPENDS_ON*0..2]-(related)
RETURN path
```

### Graph of root resources and their immediate dependencies
```cypher
MATCH (root:TerraformResource)
WHERE NOT ()-[:DEPENDS_ON]->(root)
OPTIONAL MATCH (root)-[r:DEPENDS_ON]->(dep)
RETURN root, r, dep
```

## Statistical Analysis

### Distribution of node degrees (input and output)
```cypher
MATCH (n:TerraformResource)
OPTIONAL MATCH (n)-[out:DEPENDS_ON]->()
OPTIONAL MATCH ()-[in:DEPENDS_ON]->(n)
WITH n, count(DISTINCT out) AS out_degree, count(DISTINCT in) AS in_degree
RETURN out_degree, in_degree, count(n) AS count
ORDER BY out_degree, in_degree
```

### Maximum graph depth
```cypher
MATCH path = (start:TerraformResource)-[:DEPENDS_ON*]->(end:TerraformResource)
WHERE NOT ()-[:DEPENDS_ON]->(start)
  AND NOT (end)-[:DEPENDS_ON]->()
RETURN max(length(path)) AS max_depth
```

### Graph width by level
```cypher
MATCH (root:TerraformResource)
WHERE NOT ()-[:DEPENDS_ON]->(root)
WITH root
MATCH path = (root)-[:DEPENDS_ON*]->(node)
WITH length(path) AS level, count(DISTINCT node) AS nodes_at_level
RETURN level, nodes_at_level
ORDER BY level
```

## Export and Maintenance

### List all resource names
```cypher
MATCH (n:TerraformResource)
RETURN n.name AS resource_name
ORDER BY resource_name
```

### Export structure for documentation
```cypher
MATCH (source:TerraformResource)-[r:DEPENDS_ON]->(target:TerraformResource)
RETURN source.name AS from, target.name AS to, r.label AS relationship
ORDER BY from, to
```

### Clear all data
```cypher
MATCH (n)
DETACH DELETE n
```

### Verify integrity (resources without ID)
```cypher
MATCH (n:TerraformResource)
WHERE n.id IS NULL OR n.id = ''
RETURN n
```

## Advanced Queries

### Find disconnected components
```cypher
MATCH (n:TerraformResource)
WITH collect(n) AS all_nodes
MATCH (start:TerraformResource)
WHERE NOT ()-[:DEPENDS_ON]->(start)
WITH all_nodes, collect(DISTINCT start) AS roots
UNWIND roots AS root
MATCH path = (root)-[:DEPENDS_ON*0..]->(connected)
WITH all_nodes, collect(DISTINCT connected) AS connected_from_root
UNWIND all_nodes AS node
WHERE NOT node IN connected_from_root
RETURN node.name AS disconnected_resource
```

### Graph density
```cypher
MATCH (n:TerraformResource)
WITH count(n) AS nodes
MATCH ()-[r:DEPENDS_ON]->()
WITH nodes, count(r) AS edges
RETURN nodes, edges, 
       toFloat(edges) / (nodes * (nodes - 1)) AS density
```

### Search resources by name pattern
```cypher
MATCH (n:TerraformResource)
WHERE n.name =~ '.*database.*'
RETURN n.name AS resource, n.label AS label
ORDER BY n.name
```
