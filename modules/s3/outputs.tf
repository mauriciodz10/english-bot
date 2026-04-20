output "bucket_id" {
  description = "ID del bucket S3"
  value       = aws_s3_bucket.this.id
}

output "bucket_arn" {
  description = "ARN del bucket S3 (necesario para las políticas IAM de Lambda)"
  value       = aws_s3_bucket.this.arn
}

output "bucket_name" {
  description = "Nombre del bucket"
  value       = aws_s3_bucket.this.bucket
}
