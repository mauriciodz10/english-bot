# English Bot 🇬🇧

Bot de aprendizaje de inglés que envía lecciones diarias automáticas a un grupo de Telegram, construido con AWS, Terraform, GitHub Actions y Amazon Bedrock.

Cada día (lunes a sábado) el bot envía:
- **9:30am (COT)** — 3 palabras de vocabulario nivel B2/C1
- **2:30pm (COT)** — 2 verbos irregulares con formas y ejemplos en 5 tiempos gramaticales
- **8:30pm (COT)** — 2 phrasal verbs con significado, ejemplos en contexto y tips de uso

Las lecciones son generadas por IA (Amazon Nova Micro vía Bedrock) y publicadas automáticamente en un grupo de Telegram.

---

## Arquitectura

```
GitHub Actions (CI/CD)
    └── Terraform → AWS
            ├── EventBridge Scheduler (9:30am / 2:30pm / 8:30pm COT — Lun a Sáb)
            │       └── Lambda (orquestador)
            │               ├── S3 (listas de verbos y vocabulario)
            │               ├── DynamoDB (estado — evita repetir items)
            │               ├── Bedrock / Nova Micro (generación con IA)
            │               ├── SSM Parameter Store (credenciales)
            │               └── Telegram Bot API → Grupo de Telegram
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
| Almacenamiento | S3 (listas de items), DynamoDB (estado) |
| Secretos | SSM Parameter Store |
| Scheduling | EventBridge Scheduler (Lun-Sáb) |
| Mensajería | Telegram Bot API |
| Observabilidad | CloudWatch Dashboard + Alarmas + SNS Email |

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
│   ├── s3/                     # Bucket para listas de verbos y vocabulario
│   ├── dynamodb/               # Tabla de estado (items ya enviados)
│   ├── iam/                    # Rol y políticas para Lambda
│   ├── lambda/                 # Función Lambda orquestadora
│   ├── scheduler/              # EventBridge Schedules (3 tareas, Lun-Sáb)
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
│   └── telegram_sender.py      # Publicación en grupo de Telegram
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
- Bot de Telegram creado con @BotFather

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

### 5. Cargar credenciales en SSM

```bash
# Telegram
aws ssm put-parameter \
  --name "/english-bot/dev/telegram_bot_token" \
  --value "TU_BOT_TOKEN" \
  --type SecureString --overwrite

aws ssm put-parameter \
  --name "/english-bot/dev/telegram_chat_id" \
  --value "-100XXXXXXXXXX" \
  --type String --overwrite
```

### 6. Confirmar suscripción email de SNS

Después del apply, AWS envía un email con asunto `AWS Notification - Subscription Confirmation`. Haz clic en el link para activar las alertas.

---

## Configurar el bot de Telegram

### 1. Crear el bot

1. Abre Telegram y busca `@BotFather`
2. Envía `/newbot` y sigue las instrucciones
3. Guarda el token que te entrega BotFather

### 2. Crear el grupo y obtener el Chat ID

1. Crea un grupo en Telegram y agrega el bot como administrador
2. Envía un mensaje en el grupo
3. Obtén el Chat ID:

```bash
curl "https://api.telegram.org/botTU_TOKEN/getUpdates"
# Busca el campo "chat":{"id": ...} — será un número negativo
```

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

# Dry-run (genera lección sin publicar en Telegram)
python3 scripts/test_local.py --type vocabulary --dry-run
python3 scripts/test_local.py --type irregular_verbs --dry-run
python3 scripts/test_local.py --type phrasal_verbs --dry-run

# Prueba completa con publicación real en Telegram
python3 scripts/test_local.py --type vocabulary
```

## Invocar la Lambda manualmente

```bash
# Vocabulario
aws lambda invoke \
  --function-name english-bot-dev-bot \
  --payload '{"lesson_type":"vocabulary","schedule":"morning"}' \
  --cli-binary-format raw-in-base64-out \
  response.json && cat response.json

# Verbos irregulares
aws lambda invoke \
  --function-name english-bot-dev-bot \
  --payload '{"lesson_type":"irregular_verbs","schedule":"afternoon"}' \
  --cli-binary-format raw-in-base64-out \
  response.json && cat response.json

# Phrasal verbs
aws lambda invoke \
  --function-name english-bot-dev-bot \
  --payload '{"lesson_type":"phrasal_verbs","schedule":"evening"}' \
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

## Resetear el estado de un tipo de lección

Si quieres que el bot vuelva a empezar desde el principio de la lista:

```bash
# Resetear vocabulario
aws dynamodb delete-item \
  --table-name english-bot-sent-log-dev \
  --key '{"PK": {"S": "vocabulary"}, "SK": {"S": "state"}}'

# Resetear verbos irregulares
aws dynamodb delete-item \
  --table-name english-bot-sent-log-dev \
  --key '{"PK": {"S": "irregular_verbs"}, "SK": {"S": "state"}}'

# Resetear phrasal verbs
aws dynamodb delete-item \
  --table-name english-bot-sent-log-dev \
  --key '{"PK": {"S": "phrasal_verbs"}, "SK": {"S": "state"}}'
```

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

## Lecciones del día

| Hora (COT) | Días | Tipo | Items |
|-----------|------|------|-------|
| 9:30am | Lun — Sáb | Vocabulario B2/C1 | 3 palabras |
| 2:30pm | Lun — Sáb | Verbos irregulares | 2 verbos |
| 8:30pm | Lun — Sáb | Phrasal verbs | 2 phrasal verbs |
