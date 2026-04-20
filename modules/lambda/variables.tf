variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "aws_region" {
  type = string
}

variable "lambda_role_arn" {
  description = "ARN del IAM Role que asume la función Lambda"
  type        = string
}

variable "source_dir" {
  description = "Directorio con el código fuente de la Lambda"
  type        = string
}

variable "s3_bucket_name" {
  description = "Nombre del bucket S3 con la lista de verbos"
  type        = string
}

variable "dynamodb_table_name" {
  description = "Nombre de la tabla DynamoDB de log de verbos"
  type        = string
}

variable "bedrock_model_id" {
  description = "ID del modelo Bedrock a invocar"
  type        = string
  default     = "anthropic.claude-haiku-4-5-20251001"
}

variable "tags" {
  type    = map(string)
  default = {}
}
