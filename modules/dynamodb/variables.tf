variable "table_name" {
  description = "Nombre de la tabla DynamoDB"
  type        = string
}

variable "hash_key" {
  description = "Partition key de la tabla"
  type        = string
  default     = "PK"
}

variable "range_key" {
  description = "Sort key de la tabla (dejar vacío si no se necesita)"
  type        = string
  default     = ""
}

variable "ttl_attribute" {
  description = "Nombre del atributo TTL (dejar vacío para deshabilitar)"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Tags comunes"
  type        = map(string)
  default     = {}
}
