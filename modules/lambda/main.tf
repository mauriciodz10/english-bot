##############################################################
# modules/lambda/main.tf
##############################################################

# ZIP del código Lambda
# output_path usa path.root (raíz del workspace de Terraform) en lugar de
# path.module (directorio del módulo) para que funcione tanto en local
# como en el runner efímero de GitHub Actions.
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = var.source_dir
  output_path = "${path.root}/lambda_package.zip"
}

resource "aws_lambda_function" "this" {
  function_name = "${var.project_name}-${var.environment}-bot"
  role          = var.lambda_role_arn
  handler       = "handler.lambda_handler"
  runtime       = "python3.12"
  timeout       = 30
  memory_size   = 256

  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  environment {
    variables = {
      ENVIRONMENT      = var.environment
      PROJECT_NAME     = var.project_name
      S3_BUCKET        = var.s3_bucket_name
      DYNAMODB_TABLE   = var.dynamodb_table_name
      AWS_REGION_NAME  = var.aws_region
      BEDROCK_MODEL_ID = var.bedrock_model_id
      SSM_PREFIX       = "/${var.project_name}/${var.environment}"
    }
  }

  tags = merge(var.tags, {
    Module = "lambda"
  })
}

# Permite que EventBridge Scheduler invoque esta Lambda
resource "aws_lambda_permission" "scheduler" {
  statement_id  = "AllowEventBridgeScheduler"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.this.function_name
  principal     = "scheduler.amazonaws.com"
}

# Log group con retención de 30 días
resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${aws_lambda_function.this.function_name}"
  retention_in_days = 30

  tags = var.tags
}