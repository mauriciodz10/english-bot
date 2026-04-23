##############################################################
# modules/observability/main.tf
# Crea:
#   1. SNS Topic para notificaciones de alerta
#   2. Suscripción email al topic
#   3. Tres alarmas CloudWatch:
#      - Errores de Lambda
#      - Duración alta
#      - Zero invocations (no se disparó en el día)
#   4. CloudWatch Dashboard con métricas clave
##############################################################

# ── SNS Topic central de alertas ─────────────────────────────────────────────
resource "aws_sns_topic" "alerts" {
  name = "${var.project_name}-${var.environment}-alerts"
  tags = var.tags
}

# ── Suscripción email ─────────────────────────────────────────────────────────
resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# ── ALARMA 1: Errores de Lambda ───────────────────────────────────────────────
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "${var.project_name}-${var.environment}-lambda-errors"
  alarm_description   = "La Lambda del bot generó errores"
  namespace           = "AWS/Lambda"
  metric_name         = "Errors"
  dimensions          = { FunctionName = var.lambda_function_name }
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"

  alarm_actions = [aws_sns_topic.alerts.arn]
  ok_actions    = [aws_sns_topic.alerts.arn]

  tags = var.tags
}

# ── ALARMA 2: Duración alta ───────────────────────────────────────────────────
resource "aws_cloudwatch_metric_alarm" "lambda_duration" {
  alarm_name          = "${var.project_name}-${var.environment}-lambda-duration"
  alarm_description   = "La Lambda tardó más de 20 segundos (posible problema con Bedrock o Twilio)"
  namespace           = "AWS/Lambda"
  metric_name         = "Duration"
  dimensions          = { FunctionName = var.lambda_function_name }
  statistic           = "Maximum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 20000
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"

  alarm_actions = [aws_sns_topic.alerts.arn]

  tags = var.tags
}

# ── ALARMA 3: Zero invocations ────────────────────────────────────────────────
resource "aws_cloudwatch_metric_alarm" "lambda_no_invocations" {
  alarm_name          = "${var.project_name}-${var.environment}-no-invocations"
  alarm_description   = "La Lambda no se invocó en las últimas 24 horas — revisar EventBridge Scheduler"
  namespace           = "AWS/Lambda"
  metric_name         = "Invocations"
  dimensions          = { FunctionName = var.lambda_function_name }
  statistic           = "Sum"
  period              = 86400
  evaluation_periods  = 1
  threshold           = 1
  comparison_operator = "LessThanThreshold"
  treat_missing_data  = "breaching"

  alarm_actions = [aws_sns_topic.alerts.arn]

  tags = var.tags
}

# ── CloudWatch Dashboard ──────────────────────────────────────────────────────
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.project_name}-${var.environment}"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "text"
        x      = 0
        y      = 0
        width  = 24
        height = 2
        properties = {
          markdown = "# 🇬🇧 English Bot — Dashboard\nMonitoreo en tiempo real del bot de aprendizaje de inglés."
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 2
        width  = 8
        height = 6
        properties = {
          title  = "Invocaciones diarias"
          view   = "timeSeries"
          period = 86400
          region = var.aws_region
          metrics = [[
            "AWS/Lambda", "Invocations",
            "FunctionName", var.lambda_function_name,
            { stat = "Sum", label = "Invocaciones" }
          ]]
        }
      },
      {
        type   = "metric"
        x      = 8
        y      = 2
        width  = 8
        height = 6
        properties = {
          title  = "Errores"
          view   = "timeSeries"
          region = var.aws_region
          period = 300
          metrics = [[
            "AWS/Lambda", "Errors",
            "FunctionName", var.lambda_function_name,
            { stat = "Sum", label = "Errores", color = "#d62728" }
          ]]
        }
      },
      {
        type   = "metric"
        x      = 16
        y      = 2
        width  = 8
        height = 6
        properties = {
          title  = "Duración (ms)"
          view   = "timeSeries"
          region = var.aws_region
          period = 300
          metrics = [
            [
              "AWS/Lambda", "Duration",
              "FunctionName", var.lambda_function_name,
              { stat = "Average", label = "Promedio" }
            ],
            [
              "AWS/Lambda", "Duration",
              "FunctionName", var.lambda_function_name,
              { stat = "Maximum", label = "Máximo", color = "#ff7f0e" }
            ]
          ]
        }
      },
      {
        type   = "alarm"
        x      = 0
        y      = 8
        width  = 24
        height = 3
        properties = {
          title = "Estado de alarmas"
          alarms = [
            aws_cloudwatch_metric_alarm.lambda_errors.arn,
            aws_cloudwatch_metric_alarm.lambda_duration.arn,
            aws_cloudwatch_metric_alarm.lambda_no_invocations.arn,
          ]
        }
      },
      {
        type   = "log"
        x      = 0
        y      = 11
        width  = 24
        height = 8
        properties = {
          title  = "Logs recientes"
          view   = "table"
          region = var.aws_region
          query  = "SOURCE '/aws/lambda/${var.lambda_function_name}' | fields @timestamp, @message | sort @timestamp desc | limit 20"
          period = 300
        }
      }
    ]
  })
}