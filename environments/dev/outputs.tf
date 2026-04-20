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

output "morning_schedule_arn" {
  value = module.scheduler.morning_schedule_arn
}

output "afternoon_schedule_arn" {
  value = module.scheduler.afternoon_schedule_arn
}
