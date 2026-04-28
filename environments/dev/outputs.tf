output "lambda_function_name" {
  description = "Nombre de la Lambda para invocarla manualmente en pruebas"
  value       = module.lambda.function_name
}

output "lambda_function_arn" {
  value = module.lambda.function_arn
}

output "s3_bucket_name" {
  description = "Bucket con la lista de verbos"
  value       = module.s3.bucket_name
}

output "dynamodb_table_name" {
  description = "Tabla de log de verbos enviados"
  value       = module.dynamodb.table_name
}

output "vocabulary_schedule_arn" {
  description = "ARN del schedule de vocabulario (9:30am COT)"
  value       = module.scheduler.vocabulary_schedule_arn
}

output "afternoon_schedule_arn" {
  description = "ARN del schedule de verbos irregulares (2:30pm COT)"
  value       = module.scheduler.afternoon_schedule_arn
}

output "evening_schedule_arn" {
  description = "ARN del schedule de phrasal verbs (8:30pm COT)"
  value       = module.scheduler.evening_schedule_arn
}

output "dashboard_url" {
  description = "URL del CloudWatch Dashboard"
  value       = module.observability.dashboard_url
}

output "sns_topic_arn" {
  description = "ARN del SNS topic de alertas"
  value       = module.observability.sns_topic_arn
}