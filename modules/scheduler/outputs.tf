output "morning_schedule_arn" {
  value = aws_scheduler_schedule.morning.arn
}

output "afternoon_schedule_arn" {
  value = aws_scheduler_schedule.afternoon.arn
}
