##############################################################
# modules/dynamodb/main.tf
# Crea una tabla DynamoDB con billing PAY_PER_REQUEST.
# Usada para:
#   1. Log de verbos/phrasal verbs ya enviados (evitar repetir)
#   2. Historial de lecciones por fecha
##############################################################

resource "aws_dynamodb_table" "this" {
  name         = var.table_name
  billing_mode = "PAY_PER_REQUEST" # Sin costos fijos, ideal para baja frecuencia
  hash_key     = var.hash_key
  range_key    = var.range_key != "" ? var.range_key : null

  attribute {
    name = var.hash_key
    type = "S"
  }

  dynamic "attribute" {
    for_each = var.range_key != "" ? [var.range_key] : []
    content {
      name = attribute.value
      type = "S"
    }
  }

  # TTL opcional — permite expirar registros automáticamente
  dynamic "ttl" {
    for_each = var.ttl_attribute != "" ? [var.ttl_attribute] : []
    content {
      attribute_name = ttl.value
      enabled        = true
    }
  }

  tags = merge(var.tags, {
    Module = "dynamodb"
  })
}
