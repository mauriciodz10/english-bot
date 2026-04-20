variable "aws_region" {
  description = "Región AWS donde se despliega la infraestructura"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Nombre del proyecto, usado como prefijo en todos los recursos"
  type        = string
  default     = "english-bot"
}

variable "aws_account_id" {
  description = "ID de la cuenta AWS (para nombres únicos de S3)"
  type        = string
}
