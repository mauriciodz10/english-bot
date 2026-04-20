variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "lambda_arn" {
  description = "ARN de la función Lambda a invocar"
  type        = string
}

variable "tags" {
  type    = map(string)
  default = {}
}
