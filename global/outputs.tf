output "tf_state_bucket" {
  description = "Nombre del bucket S3 que almacena el remote state"
  value       = aws_s3_bucket.tf_state.bucket
}

output "tf_lock_table" {
  description = "Nombre de la tabla DynamoDB para el state locking"
  value       = aws_dynamodb_table.tf_lock.name
}
