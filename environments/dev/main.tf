##############################################################
# environments/dev/main.tf
# Orquesta todos los módulos para el environment "dev".
# Prerequisito: haber aplicado global/ primero.
##############################################################

terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Remote state en el bucket creado por global/
  # Reemplaza BUCKET_NAME con el output de: cd global && terraform output tf_state_bucket
  backend "s3" {
    bucket         = "english-bot-tf-state-032983035465" # <-- actualizar
    key            = "environments/dev/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "english-bot-tf-lock"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = local.common_tags
  }
}

locals {
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
    Team        = "devops"
  }
}

# ── 1. S3: bucket para lista de verbos y assets ──
module "s3" {
  source = "../../modules/s3"

  bucket_name        = "${var.project_name}-assets-${var.environment}-${var.aws_account_id}"
  versioning_enabled = true
  upload_verbs_file  = true # Sube los JSON de verbos al crear la infra
  tags               = local.common_tags
}

# ── 2. DynamoDB: tabla de log de verbos enviados ──
module "dynamodb" {
  source = "../../modules/dynamodb"

  table_name    = "${var.project_name}-sent-log-${var.environment}"
  hash_key      = "PK"         # Ej: "irregular_verbs" o "phrasal_verbs"
  range_key     = "SK"         # Ej: fecha ISO "2025-03-20"
  ttl_attribute = "expires_at" # Auto-expirar registros viejos (opcional)
  tags          = local.common_tags
}

# ── 3. IAM: rol y políticas para Lambda ──
module "iam" {
  source = "../../modules/iam"

  project_name   = var.project_name
  environment    = var.environment
  aws_region     = var.aws_region
  aws_account_id = var.aws_account_id

  dynamodb_table_arns = [module.dynamodb.table_arn]
  s3_bucket_arns      = [module.s3.bucket_arn]

  tags = local.common_tags
}

# ── 4. Lambda: función orquestadora del bot ──
module "lambda" {
  source = "../../modules/lambda"

  project_name        = var.project_name
  environment         = var.environment
  aws_region          = var.aws_region
  lambda_role_arn     = module.iam.lambda_role_arn
  source_dir          = "../../src"
  s3_bucket_name      = module.s3.bucket_name
  dynamodb_table_name = module.dynamodb.table_name
  bedrock_model_id    = var.bedrock_model_id
  tags                = local.common_tags
}

# ── 5. EventBridge Scheduler: disparadores AM y PM ──
module "scheduler" {
  source = "../../modules/scheduler"

  project_name = var.project_name
  environment  = var.environment
  lambda_arn   = module.lambda.function_arn
  tags         = local.common_tags
}

# ── SSM Parameters: credenciales de Twilio (se crean vacíos, se llenan manualmente) ──
resource "aws_ssm_parameter" "twilio_account_sid" {
  name  = "/${var.project_name}/${var.environment}/twilio_account_sid"
  type  = "SecureString"
  value = "PLACEHOLDER" # Actualizar manualmente en la consola AWS o con AWS CLI

  lifecycle {
    ignore_changes = [value] # Terraform no sobreescribe el valor real
  }
}

resource "aws_ssm_parameter" "twilio_auth_token" {
  name  = "/${var.project_name}/${var.environment}/twilio_auth_token"
  type  = "SecureString"
  value = "PLACEHOLDER"

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "twilio_whatsapp_from" {
  name  = "/${var.project_name}/${var.environment}/twilio_whatsapp_from"
  type  = "String"
  value = "whatsapp:+14155238886" # Número sandbox de Twilio (actualizar en prod)
}

resource "aws_ssm_parameter" "whatsapp_to" {
  name  = "/${var.project_name}/${var.environment}/whatsapp_to"
  type  = "String"
  value = "whatsapp:+57XXXXXXXXXX" # Tu número de WhatsApp con código de país
}
resource "aws_ssm_parameter" "whatsapp_recipients" {
  name  = "/${var.project_name}/${var.environment}/whatsapp_recipients"
  type  = "String"
  value = "PLACEHOLDER"

  lifecycle {
    ignore_changes = [value]
  }
}

# ── 6. Observabilidad: alarmas, dashboard y alertas ──
module "observability" {
  source = "../../modules/observability"

  project_name         = var.project_name
  environment          = var.environment
  aws_region           = var.aws_region
  aws_account_id       = var.aws_account_id
  lambda_function_name = module.lambda.function_name
  alert_email          = var.alert_email
  tags                 = local.common_tags
}
