##############################################################
# modules/scheduler/main.tf
# Tres EventBridge Schedules:
#   - 9:30am  COT (14:30 UTC) → vocabulario B2/C1
#   - 2:30pm  COT (19:30 UTC) → verbos irregulares
#   - 8:30pm  COT (01:30 UTC) → phrasal verbs
##############################################################

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

# ── 9:30am COT → Vocabulario B2/C1 ───────────────────────────────────────────
resource "aws_scheduler_schedule" "vocabulary" {
  name       = "${var.project_name}-${var.environment}-vocabulary"
  group_name = "default"

  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression          = "cron(30 14 * * ? *)"
  schedule_expression_timezone = "America/Bogota"

  target {
    arn      = var.lambda_arn
    role_arn = aws_iam_role.scheduler.arn

    input = jsonencode({
      lesson_type = "vocabulary"
      schedule    = "morning"
    })
  }
}

# ── 2:30pm COT → Verbos irregulares ──────────────────────────────────────────
resource "aws_scheduler_schedule" "afternoon" {
  name       = "${var.project_name}-${var.environment}-afternoon"
  group_name = "default"

  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression          = "cron(30 19 * * ? *)"
  schedule_expression_timezone = "America/Bogota"

  target {
    arn      = var.lambda_arn
    role_arn = aws_iam_role.scheduler.arn

    input = jsonencode({
      lesson_type = "irregular_verbs"
      schedule    = "afternoon"
    })
  }
}

# ── 8:30pm COT → Phrasal verbs ────────────────────────────────────────────────
resource "aws_scheduler_schedule" "evening" {
  name       = "${var.project_name}-${var.environment}-evening"
  group_name = "default"

  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression          = "cron(30 1 * * ? *)"
  schedule_expression_timezone = "America/Bogota"

  target {
    arn      = var.lambda_arn
    role_arn = aws_iam_role.scheduler.arn

    input = jsonencode({
      lesson_type = "phrasal_verbs"
      schedule    = "evening"
    })
  }
}
