output "sns_topic_arn" {
  description = "ARN del SNS topic de alertas"
  value       = aws_sns_topic.alerts.arn
}

output "dashboard_url" {
  description = "URL directa al CloudWatch Dashboard"
  value       = "https://${var.aws_region}.console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${aws_cloudwatch_dashboard.main.dashboard_name}"
}
