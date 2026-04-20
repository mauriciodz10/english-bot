output "lambda_role_arn" {
  description = "ARN del IAM Role que asume la Lambda"
  value       = aws_iam_role.lambda_exec.arn
}

output "lambda_role_name" {
  description = "Nombre del IAM Role"
  value       = aws_iam_role.lambda_exec.name
}
