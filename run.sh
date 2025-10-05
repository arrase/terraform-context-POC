#!/bin/bash

# Script de ejemplo para ejecutar el proyecto completo

echo "=== Terraform Graph to Neo4j Ingestion ==="
echo ""

# Verificar que estamos en un directorio de Terraform
if [ ! -f "*.tf" ] && [ ! -d ".terraform" ]; then
    echo "⚠️  Advertencia: No se detectaron archivos .tf en el directorio actual"
    echo "Asegúrate de estar en un directorio de Terraform"
fi

# Verificar que Neo4j está corriendo
echo "🔍 Verificando conexión a Neo4j..."
if ! command -v cypher-shell &> /dev/null; then
    echo "⚠️  cypher-shell no encontrado, saltando verificación de Neo4j"
else
    if cypher-shell -u neo4j -p "${NEO4J_PASSWORD:-password}" "RETURN 1" &> /dev/null; then
        echo "✓ Neo4j está accesible"
    else
        echo "❌ No se pudo conectar a Neo4j"
        echo "Asegúrate de que Neo4j esté corriendo y las credenciales sean correctas"
    fi
fi

# Ejecutar el script principal
echo ""
echo "🚀 Iniciando ingesta del grafo de Terraform..."
echo ""

python main.py "$@"
