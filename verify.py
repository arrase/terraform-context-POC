#!/usr/bin/env python3
"""
Script de verificación para comprobar que los datos están correctamente ingested en Neo4j.
"""

import os
from dotenv import load_dotenv
from neo4j_connector import Neo4jConnector

# Cargar variables de entorno
load_dotenv()

neo4j_uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
neo4j_user = os.getenv('NEO4J_USER', 'neo4j')
neo4j_password = os.getenv('NEO4J_PASSWORD')

print("🔍 Verificando datos en Neo4j...\n")

with Neo4jConnector(neo4j_uri, neo4j_user, neo4j_password) as connector:
    # Obtener estadísticas
    stats = connector.get_stats()
    print(f"📊 Estadísticas de la base de datos:")
    print(f"   - Nodos: {stats['nodes']}")
    print(f"   - Relaciones: {stats['relationships']}")
    print()
    
    # Listar todos los recursos
    with connector.driver.session() as session:
        result = session.run("""
            MATCH (n:TerraformResource)
            RETURN n.name AS name, n.id AS id
            ORDER BY n.name
        """)
        
        print("📋 Recursos de Terraform encontrados:")
        for record in result:
            print(f"   - {record['name']} (ID: {record['id']})")
        print()
        
        # Listar dependencias
        result = session.run("""
            MATCH (source:TerraformResource)-[r:DEPENDS_ON]->(target:TerraformResource)
            RETURN source.name AS from, target.name AS to
            ORDER BY from, to
        """)
        
        print("🔗 Dependencias encontradas:")
        dependencies = list(result)
        if dependencies:
            for record in dependencies:
                print(f"   - {record['from']} → {record['to']}")
        else:
            print("   No se encontraron dependencias directas")

print("\n✅ Verificación completada!")
