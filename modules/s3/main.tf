##############################################################
# modules/s3/main.tf
# Crea un bucket S3 privado con versionado y encriptación.
# Reutilizable para cualquier bucket del proyecto.
##############################################################

resource "aws_s3_bucket" "this" {
  bucket = var.bucket_name

  tags = merge(var.tags, {
    Module = "s3"
  })
}

resource "aws_s3_bucket_versioning" "this" {
  bucket = aws_s3_bucket.this.id
  versioning_configuration {
    status = var.versioning_enabled ? "Enabled" : "Suspended"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "this" {
  bucket = aws_s3_bucket.this.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "this" {
  bucket                  = aws_s3_bucket.this.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Subir el archivo JSON con la lista de verbos irregulares
resource "aws_s3_object" "verbs_file" {
  count   = var.upload_verbs_file ? 1 : 0
  bucket  = aws_s3_bucket.this.id
  key     = "data/irregular_verbs.json"
  content = jsonencode(var.irregular_verbs_list)
  content_type = "application/json"
}

# Subir el archivo JSON con la lista de phrasal verbs
resource "aws_s3_object" "phrasal_verbs_file" {
  count   = var.upload_verbs_file ? 1 : 0
  bucket  = aws_s3_bucket.this.id
  key     = "data/phrasal_verbs.json"
  content = jsonencode(var.phrasal_verbs_list)
  content_type = "application/json"
}
