variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "aws_region" {
  type = string
}

variable "aws_account_id" {
  type = string
}

variable "lambda_function_name" {
  description = "Nombre de la Lambda principal del bot"
  type        = string
}

variable "alert_email" {
  description = "Email para recibir notificaciones de alerta"
  type        = string
}

variable "tags" {
  type    = map(string)
  default = {}
}
