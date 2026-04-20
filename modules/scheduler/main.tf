##############################################################
# modules/scheduler/main.tf
# Crea dos EventBridge Schedules:
#   - Mañana: 8:00am COT (13:00 UTC) → verbos irregulares
#   - Tarde:  3:00pm COT (20:00 UTC) → phrasal verbs
# COT = UTC-5
##############################################################

# Rol IAM que EventBridge asume para invocar Lambda
data "aws_iam_policy_document" "scheduler_trust" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["scheduler.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "scheduler" {
  name               = "${var.project_name}-${var.environment}-scheduler-role"
  assume_role_policy = data.aws_iam_policy_document.scheduler_trust.json
  tags               = var.tags
}

data "aws_iam_policy_document" "invoke_lambda" {
  statement {
    effect    = "Allow"
    actions   = ["lambda:InvokeFunction"]
    resources = [var.lambda_arn]
  }
}

resource "aws_iam_role_policy" "invoke_lambda" {
  name   = "invoke-lambda"
  role   = aws_iam_role.scheduler.id
  policy = data.aws_iam_policy_document.invoke_lambda.json
}

# ── Schedule de la MAÑANA: verbos irregulares (8:00am COT = 13:00 UTC) ──
resource "aws_scheduler_schedule" "morning" {
  name       = "${var.project_name}-${var.environment}-morning"
  group_name = "default"

  flexible_time_window {
    mode = "OFF"  # Disparo exacto, sin ventana flexible
  }

  # Cron: minuto 0, hora 13 UTC, cada día
  schedule_expression          = "cron(0 13 * * ? *)"
  schedule_expression_timezone = "America/Bogota"

  target {
    arn      = var.lambda_arn
    role_arn = aws_iam_role.scheduler.arn

    # Payload que recibe Lambda para saber qué tipo de lección generar
    input = jsonencode({
      lesson_type = "irregular_verbs"
      schedule    = "morning"
    })
  }
}

# ── Schedule de la TARDE: phrasal verbs (3:00pm COT = 20:00 UTC) ──
resource "aws_scheduler_schedule" "afternoon" {
  name       = "${var.project_name}-${var.environment}-afternoon"
  group_name = "default"

  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression          = "cron(0 20 * * ? *)"
  schedule_expression_timezone = "America/Bogota"

  target {
    arn      = var.lambda_arn
    role_arn = aws_iam_role.scheduler.arn

    input = jsonencode({
      lesson_type = "phrasal_verbs"
      schedule    = "afternoon"
    })
  }
}
