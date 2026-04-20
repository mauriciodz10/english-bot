##############################################################
# global/main.tf
# Infraestructura compartida: remote state backend
# Se aplica UNA SOLA VEZ antes que cualquier environment.
# Comando: cd global && terraform init && terraform apply
##############################################################

terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  # El global no usa remote state (es quien lo crea)
}

provider "aws" {
  region = var.aws_region
}

# ── S3 bucket para almacenar el terraform.tfstate de cada environment ──
resource "aws_s3_bucket" "tf_state" {
  bucket = "${var.project_name}-tf-state-${var.aws_account_id}"

  tags = {
    Project     = var.project_name
    ManagedBy   = "terraform"
    Environment = "global"
  }
}

resource "aws_s3_bucket_versioning" "tf_state" {
  bucket = aws_s3_bucket.tf_state.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "tf_state" {
  bucket = aws_s3_bucket.tf_state.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "tf_state" {
  bucket                  = aws_s3_bucket.tf_state.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ── DynamoDB para locking del state (evita apply concurrentes) ──
resource "aws_dynamodb_table" "tf_lock" {
  name         = "${var.project_name}-tf-lock"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = {
    Project     = var.project_name
    ManagedBy   = "terraform"
    Environment = "global"
  }
}
