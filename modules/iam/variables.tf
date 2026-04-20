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

variable "dynamodb_table_arns" {
  description = "Lista de ARNs de tablas DynamoDB a las que Lambda puede acceder"
  type        = list(string)
}

variable "s3_bucket_arns" {
  description = "Lista de ARNs de buckets S3 a los que Lambda puede acceder"
  type        = list(string)
}

variable "tags" {
  type    = map(string)
  default = {}
}
