output "vocabulary_schedule_arn" {
  value = aws_scheduler_schedule.vocabulary.arn
}

output "afternoon_schedule_arn" {
  value = aws_scheduler_schedule.afternoon.arn
}

output "evening_schedule_arn" {
  value = aws_scheduler_schedule.evening.arn
}
