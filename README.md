# English Bot 🇬🇧

Bot de aprendizaje de inglés que envía lecciones diarias vía WhatsApp, construido con AWS, Terraform, GitHub Actions y Amazon Bedrock.

Cada día el bot envía automáticamente:
- **8:00am (COT)** — 2 verbos irregulares con sus formas y ejemplos en 5 tiempos gramaticales
- **3:00pm (COT)** — 2 phrasal verbs con significado, ejemplos en contexto y tips de uso

Las lecciones son generadas por IA (Amazon Nova Micro vía Bedrock) y entregadas a múltiples destinatarios en WhatsApp vía Twilio.

---

## Arquitectura

```
GitHub Actions (CI/CD)
    └── Terraform → AWS
            ├── EventBridge Scheduler (8am / 3pm COT)
            │       └── Lambda (orquestador)
            │               ├── S3 (lista de verbos)
            │               ├── DynamoDB (log de verbos enviados)
            │               ├── Bedrock / Nova Micro (generación con IA)
            │               ├── SSM Parameter Store (credenciales)
            │               └── Twilio API → WhatsApp
            └── Observabilidad
                    ├── CloudWatch Dashboard
                    ├── Alarmas (errores, duración, zero invocations)
                    └── SNS → Email
```

## Stack tecnológico

| Capa | Tecnología |
|------|-----------|
| IaC | Terraform >= 1.6 con módulos reutilizables |
| CI/CD | GitHub Actions + OIDC (sin access keys) |
| Cómputo | AWS Lambda (Python 3.12) |
| IA | Amazon Bedrock — Amazon Nova Micro |
| Almacenamiento | S3 (lista de verbos), DynamoDB (estado) |
| Secretos | SSM Parameter Store |
| Scheduling | EventBridge Scheduler |
| Mensajería | Twilio WhatsApp API |
| Observabilidad | CloudWatch Dashboard + Alarmas + SNS |

---

## Estructura del proyecto

```
english-bot/
├── .github/
│   └── workflows/
│       └── deploy.yml          # CI/CD: plan en PR, apply en merge a main
├── global/                     # Remote state backend (se aplica UNA SOLA VEZ)
│   ├── main.tf                 # S3 + DynamoDB para Terraform state
│   ├── variables.tf
│   ├── outputs.tf
│   └── terraform.tfvars
├── modules/                    # Módulos reutilizables
│   ├── s3/                     # Bucket para lista de verbos
│   ├── dynamodb/               # Tabla de log de verbos enviados
│   ├── iam/                    # Rol y políticas para Lambda
│   ├── lambda/                 # Función Lambda orquestadora
│   ├── scheduler/              # EventBridge Schedules AM y PM
│   └── observability/          # Dashboard, alarmas y SNS
├── environments/
│   └── dev/                    # Environment de desarrollo
│       ├── main.tf             # Instancia todos los módulos
│       ├── variables.tf
│       ├── outputs.tf
│       └── terraform.tfvars
├── src/                        # Código fuente de la Lambda
│   ├── handler.py              # Orquestador principal
│   ├── verb_selector.py        # Selección aleatoria sin repetir
│   ├── bedrock_generator.py    # Generación de lecciones con IA
│   └── whatsapp_sender.py      # Envío a WhatsApp vía Twilio
└── scripts/
    ├── test_local.py           # Pruebas locales sin deploy
    └── enable_bedrock.sh       # Verificación de acceso a Bedrock
```

---

## Prerrequisitos

- AWS CLI configurado (`aws configure`)
- Terraform >= 1.6.0
- Python 3.12 + pip
- Cuenta GitHub con el repo creado
- Cuenta Twilio con sandbox de WhatsApp activo

---

## Despliegue inicial

### 1. Obtener Account ID

```bash
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "Account ID: $AWS_ACCOUNT_ID"
```

### 2. Configurar variables

Reemplaza los placeholders en:
- `global/terraform.tfvars` → `aws_account_id`
- `environments/dev/terraform.tfvars` → `aws_account_id`, `alert_email`
- `environments/dev/main.tf` → bucket del backend S3

### 3. Aplicar el global (una sola vez)

```bash
cd global
terraform init
terraform apply
```

### 4. Aplicar el environment dev

```bash
cd environments/dev
terraform init
terraform apply
```

### 5. Cargar credenciales de Twilio en SSM

```bash
aws ssm put-parameter \
  --name "/english-bot/dev/twilio_account_sid" \
  --value "ACxxxxxxxxxxxxxxxx" \
  --type SecureString --overwrite

aws ssm put-parameter \
  --name "/english-bot/dev/twilio_auth_token" \
  --value "tu_auth_token" \
  --type SecureString --overwrite

aws ssm put-parameter \
  --name "/english-bot/dev/whatsapp_recipients" \
  --value "whatsapp:+57XXX,whatsapp:+57YYY" \
  --type String --overwrite
```

### 6. Confirmar suscripción email de SNS

Después del apply, AWS envía un email con asunto `AWS Notification - Subscription Confirmation`. Haz clic en el link para activar las alertas por email.

---

## CI/CD con GitHub Actions

El pipeline usa autenticación OIDC — sin access keys hardcodeadas en el repo.

### Configurar OIDC

```bash
# Crear el OIDC provider en AWS
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1

# Crear el rol para GitHub Actions
aws iam create-role \
  --role-name github-actions-english-bot \
  --assume-role-policy-document file:///tmp/github-trust-policy.json

aws iam attach-role-policy \
  --role-name github-actions-english-bot \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess
```

### Secrets en GitHub

En Settings → Secrets and variables → Actions:

| Secret | Valor |
|--------|-------|
| `AWS_ROLE_ARN` | `arn:aws:iam::ACCOUNT_ID:role/github-actions-english-bot` |
| `AWS_ACCOUNT_ID` | Tu Account ID de AWS |

### Flujo del pipeline

```
Pull Request → terraform fmt + validate + plan  (resultado como comentario en el PR)
Merge a main → terraform apply automático
```

---

## Pruebas locales

```bash
# Crear entorno virtual
python3 -m venv .venv && source .venv/bin/activate
pip install boto3

# Dry-run (genera lección sin enviar a WhatsApp)
python3 scripts/test_local.py --type irregular_verbs --dry-run
python3 scripts/test_local.py --type phrasal_verbs --dry-run

# Prueba completa con envío real
python3 scripts/test_local.py --type irregular_verbs
```

## Invocar la Lambda manualmente

```bash
aws lambda invoke \
  --function-name english-bot-dev-bot \
  --payload '{"lesson_type":"irregular_verbs","schedule":"morning"}' \
  --cli-binary-format raw-in-base64-out \
  response.json && cat response.json

# Ver logs en tiempo real
aws logs tail /aws/lambda/english-bot-dev-bot --follow
```

---

## Observabilidad

```bash
# Ver URL del dashboard
terraform output dashboard_url

# Ver estado de las alarmas
aws cloudwatch describe-alarms \
  --alarm-name-prefix "english-bot-dev" \
  --query "MetricAlarms[].{Nombre:AlarmName,Estado:StateValue}" \
  --output table
```

### Alarmas configuradas

| Alarma | Condición | Acción |
|--------|-----------|--------|
| `lambda-errors` | >= 1 error en 5 min | Email |
| `lambda-duration` | > 20 segundos | Email |
| `no-invocations` | 0 invocaciones en 24h | Email |

---

## Destruir la infraestructura

```bash
# 1. Destruir el environment primero
cd environments/dev
terraform destroy

# 2. Vaciar buckets S3 antes de destruir el global
aws s3 rm s3://english-bot-assets-dev-ACCOUNT_ID --recursive
aws s3 rm s3://english-bot-tf-state-ACCOUNT_ID --recursive

# 3. Destruir el global
cd ../../global
terraform destroy
```

---

## Fases del proyecto

| Fase | Descripción |
|------|-------------|
| 1 | Infraestructura base con Terraform modular + CI/CD con GitHub Actions + OIDC |
| 2 | Lambda + Amazon Bedrock (Nova Micro) + selección aleatoria sin repetir |
| 3 | Integración WhatsApp vía Twilio + múltiples destinatarios + secretos en SSM |
| 4 | CloudWatch Dashboard + alarmas + notificaciones SNS por email |
