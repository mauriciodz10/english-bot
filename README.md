# English Sori Bot — DevOps Project

Bot de aprendizaje de inglés que envía lecciones diarias vía WhatsApp,
construido con AWS, Terraform, GitHub Actions y Amazon Bedrock.

## Estructura del proyecto

```
english-bot/
├── .github/
│   └── workflows/
│       └── deploy.yml          # CI/CD pipeline
├── global/                     # Remote state backend (se aplica UNA SOLA VEZ)
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── terraform.tfvars
├── modules/                    # Módulos reutilizables
│   ├── s3/                     # Bucket para lista de verbos
│   ├── dynamodb/               # Tabla de log de verbos enviados
│   ├── iam/                    # Rol y políticas para Lambda
│   ├── lambda/                 # Función Lambda orquestadora
│   └── scheduler/              # EventBridge Schedules AM y PM
├── environments/
│   └── dev/                    # Environment de desarrollo
│       ├── main.tf             # Instancia todos los módulos
│       ├── variables.tf
│       ├── outputs.tf
│       └── terraform.tfvars
└── src/
    └── handler.py              # Código Lambda (placeholder en Fase 1)
```

## Prerrequisitos

- AWS CLI configurado (`aws configure`)
- Terraform >= 1.6.0
- Python 3.12
- Cuenta en GitHub con el repo creado

## Fase 1: Despliegue inicial

### Paso 1 — Obtener tu Account ID

```bash
aws sts get-caller-identity --query Account --output text
```

Reemplaza `TU_ACCOUNT_ID_AQUI` en:
- `global/terraform.tfvars`
- `environments/dev/terraform.tfvars`
- `environments/dev/main.tf` (el backend S3)

### Paso 2 — Aplicar el global (solo la primera vez)

```bash
cd global
terraform init
terraform apply
```

Esto crea el bucket S3 de remote state y la tabla DynamoDB de locking.
Anota el output `tf_state_bucket` y actualízalo en el backend de `environments/dev/main.tf`.

### Paso 3 — Inicializar y aplicar el environment dev

```bash
cd ../environments/dev
terraform init
terraform plan
terraform apply
```

### Paso 4 — Verificar los recursos creados

```bash
# Ver outputs
terraform output

# Invocar la Lambda manualmente para confirmar que funciona
aws lambda invoke \
  --function-name english-bot-dev-bot \
  --payload '{"lesson_type":"irregular_verbs","schedule":"morning"}' \
  --cli-binary-format raw-in-base64-out \
  response.json && cat response.json

# Ver logs de la invocación
aws logs tail /aws/lambda/english-bot-dev-bot --follow
```

### Paso 5 — Cargar las credenciales de Twilio en SSM

```bash
# Obtenlas en: https://console.twilio.com
aws ssm put-parameter \
  --name "/english-bot/dev/twilio_account_sid" \
  --value "ACxxxxxxxxxxxxxxxx" \
  --type SecureString \
  --overwrite

aws ssm put-parameter \
  --name "/english-bot/dev/twilio_auth_token" \
  --value "tu_auth_token" \
  --type SecureString \
  --overwrite

# Actualizar tu número de WhatsApp destino
aws ssm put-parameter \
  --name "/english-bot/dev/whatsapp_to" \
  --value "whatsapp:+57XXXXXXXXXX" \
  --type String \
  --overwrite
```

## Configurar GitHub Actions (CI/CD)

### 1. Crear el OIDC provider en AWS

```bash
# Permite que GitHub Actions se autentique en AWS sin access keys
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1
```

### 2. Crear el IAM Role para GitHub Actions

Crea un rol `github-actions-english-bot` con este trust policy
(reemplaza `TU_GITHUB_USER` y `TU_REPO`):

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {
      "Federated": "arn:aws:iam::TU_ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
    },
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {
      "StringEquals": {
        "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
      },
      "StringLike": {
        "token.actions.githubusercontent.com:sub": "repo:TU_GITHUB_USER/TU_REPO:*"
      }
    }
  }]
}
```

Adjunta la política `AdministratorAccess` al rol (en prod usar mínimo privilegio).

### 3. Agregar secrets en GitHub

En tu repo: Settings → Secrets and variables → Actions

| Secret | Valor |
|--------|-------|
| `AWS_ROLE_ARN` | `arn:aws:iam::TU_ACCOUNT_ID:role/github-actions-english-bot` |
| `AWS_ACCOUNT_ID` | Tu Account ID de AWS |

## Flujo CI/CD

```
Pull Request → terraform fmt + validate + plan  (resultado como comentario en el PR)
Merge a main → terraform apply automático
```

## Fases del proyecto

| Fase | Descripción | Estado |
|------|-------------|--------|
| 1 | Infraestructura base (Terraform + CI/CD) | ✅ Esta fase |
| 2 | Lambda + Amazon Bedrock (generación de lecciones) | Pendiente |
| 3 | Integración Twilio → WhatsApp | Pendiente |
| 4 | Observabilidad (CloudWatch + alarmas) | Pendiente |
