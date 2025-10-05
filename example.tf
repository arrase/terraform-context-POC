# Ejemplo de configuración de Terraform para pruebas
# Este archivo crea recursos de ejemplo para generar un grafo

terraform {
  required_version = ">= 1.0"
}

# Recurso de ejemplo: Grupo de recursos
resource "null_resource" "ejemplo_1" {
  triggers = {
    timestamp = timestamp()
  }
}

# Recurso que depende del anterior
resource "null_resource" "ejemplo_2" {
  depends_on = [null_resource.ejemplo_1]
  
  triggers = {
    parent = null_resource.ejemplo_1.id
  }
}

# Otro recurso independiente
resource "null_resource" "ejemplo_3" {
  triggers = {
    value = "test"
  }
}

# Recurso que depende de múltiples recursos
resource "null_resource" "ejemplo_final" {
  depends_on = [
    null_resource.ejemplo_2,
    null_resource.ejemplo_3
  ]
  
  triggers = {
    combined = "${null_resource.ejemplo_2.id}-${null_resource.ejemplo_3.id}"
  }
}

output "ejemplo_output" {
  value = null_resource.ejemplo_final.id
}
