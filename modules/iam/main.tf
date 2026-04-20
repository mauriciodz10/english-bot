##############################################################
# modules/iam/main.tf
# Crea el IAM Role que asume Lambda, con políticas de mínimo
# privilegio para cada servicio que necesita consumir.
##############################################################

# Trust policy: permite que el servicio Lambda asuma este rol
data "aws_iam_policy_document" "lambda_trust" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda_exec" {
  name               = "${var.project_name}-${var.environment}-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_trust.json

  tags = var.tags
}

# ── Política: CloudWatch Logs (obligatoria para ver logs de Lambda) ──
resource "aws_iam_role_policy_attachment" "basic_execution" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# ── Política: Amazon Bedrock (invocar modelos de IA) ──
data "aws_iam_policy_document" "bedrock" {
  statement {
    effect    = "Allow"
    actions   = ["bedrock:InvokeModel"]
    resources = ["arn:aws:bedrock:${var.aws_region}::foundation-model/*"]
  }
}

resource "aws_iam_policy" "bedrock" {
  name   = "${var.project_name}-${var.environment}-bedrock-policy"
  policy = data.aws_iam_policy_document.bedrock.json
}

resource "aws_iam_role_policy_attachment" "bedrock" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.bedrock.arn
}

# ── Política: DynamoDB (leer/escribir la tabla de verbos enviados) ──
data "aws_iam_policy_document" "dynamodb" {
  statement {
    effect = "Allow"
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:Query",
      "dynamodb:Scan"
    ]
    resources = var.dynamodb_table_arns
  }
}

resource "aws_iam_policy" "dynamodb" {
  name   = "${var.project_name}-${var.environment}-dynamodb-policy"
  policy = data.aws_iam_policy_document.dynamodb.json
}

resource "aws_iam_role_policy_attachment" "dynamodb" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.dynamodb.arn
}

# ── Política: S3 (leer lista de verbos) ──
data "aws_iam_policy_document" "s3" {
  statement {
    effect    = "Allow"
    actions   = ["s3:GetObject", "s3:ListBucket"]
    resources = concat(var.s3_bucket_arns, [for arn in var.s3_bucket_arns : "${arn}/*"])
  }
}

resource "aws_iam_policy" "s3" {
  name   = "${var.project_name}-${var.environment}-s3-policy"
  policy = data.aws_iam_policy_document.s3.json
}

resource "aws_iam_role_policy_attachment" "s3" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.s3.arn
}

# ── Política: SSM Parameter Store (leer credenciales de Twilio) ──
data "aws_iam_policy_document" "ssm" {
  statement {
    effect    = "Allow"
    actions   = ["ssm:GetParameter", "ssm:GetParameters"]
    resources = ["arn:aws:ssm:${var.aws_region}:${var.aws_account_id}:parameter/${var.project_name}/*"]
  }
}

resource "aws_iam_policy" "ssm" {
  name   = "${var.project_name}-${var.environment}-ssm-policy"
  policy = data.aws_iam_policy_document.ssm.json
}

resource "aws_iam_role_policy_attachment" "ssm" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.ssm.arn
}
