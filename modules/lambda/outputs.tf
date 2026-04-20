output "function_arn" {
  description = "ARN de la función Lambda"
  value       = aws_lambda_function.this.arn
}

output "function_name" {
  description = "Nombre de la función Lambda"
  value       = aws_lambda_function.this.function_name
}

output "invoke_arn" {
  description = "ARN de invocación (útil para API Gateway en fases futuras)"
  value       = aws_lambda_function.this.invoke_arn
}
