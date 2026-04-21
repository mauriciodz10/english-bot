variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "project_name" {
  type    = string
  default = "english-bot"
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "aws_account_id" {
  description = "ID de la cuenta AWS"
  type        = string
}

variable "bedrock_model_id" {
  description = "Modelo de Bedrock para generar las lecciones"
  type        = string
  default     = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
}
