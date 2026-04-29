"""
handler.py — Fase final
Orquestador principal de la Lambda del English Bot.

Flujo:
  1. Recibe evento de EventBridge Scheduler (lesson_type + schedule)
  2. VerbSelector elige items sin repetir (S3 + DynamoDB)
  3. BedrockGenerator produce la explicación con Amazon Nova Micro
  4. TelegramSender publica el mensaje en el grupo de Telegram
"""

import json
import logging
import os

from bedrock_generator import BedrockGenerator
from verb_selector import VerbSelector
from telegram_sender import TelegramSender

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# ── Variables de entorno ──────────────────────────────────────────────────────
S3_BUCKET        = os.environ["S3_BUCKET"]
DYNAMODB_TABLE   = os.environ["DYNAMODB_TABLE"]
AWS_REGION_NAME  = os.environ["AWS_REGION_NAME"]
BEDROCK_MODEL_ID = os.environ["BEDROCK_MODEL_ID"]
SSM_PREFIX       = os.environ["SSM_PREFIX"]
ENVIRONMENT      = os.environ.get("ENVIRONMENT", "dev")

# ── Clientes (reutilización entre invocaciones) ───────────────────────────────
verb_selector = VerbSelector(
    s3_bucket      = S3_BUCKET,
    dynamodb_table = DYNAMODB_TABLE,
    aws_region     = AWS_REGION_NAME,
)

bedrock_generator = BedrockGenerator(
    model_id   = BEDROCK_MODEL_ID,
    aws_region = AWS_REGION_NAME,
)

telegram_sender = TelegramSender(
    ssm_prefix = SSM_PREFIX,
    aws_region = AWS_REGION_NAME,
)


def lambda_handler(event: dict, context) -> dict:
    logger.info("english-bot invocado | event: %s", json.dumps(event))

    # ── 1. Validar evento ─────────────────────────────────────────────────────
    lesson_type = event.get("lesson_type")
    schedule    = event.get("schedule")

    if lesson_type not in ("irregular_verbs", "phrasal_verbs", "vocabulary"):
        raise ValueError(f"lesson_type inválido: '{lesson_type}'.")

    logger.info("Procesando lección — tipo: %s | horario: %s", lesson_type, schedule)

    # ── 2. Seleccionar items ──────────────────────────────────────────────────
    count          = 3 if lesson_type == "vocabulary" else 2
    selected_items, cycle = verb_selector.select(lesson_type, count=count)
    logger.info("Items seleccionados: %s | Ciclo: %d", selected_items, cycle)

    # ── 3. Generar lección con Bedrock ────────────────────────────────────────
    lesson_content = bedrock_generator.generate(lesson_type, selected_items)

    # ── 4. Construir mensaje ──────────────────────────────────────────────────
    message = bedrock_generator.build_whatsapp_message(
        lesson_type    = lesson_type,
        verbs          = selected_items,
        lesson_content = lesson_content,
        cycle          = cycle,
    )

    # ── 5. Enviar a Telegram ──────────────────────────────────────────────────
    result = telegram_sender.send(message)

    logger.info(
        "Lección enviada — tipo: %s | items: %s | telegram_msg_id: %s",
        lesson_type, selected_items, result["message_id"],
    )

    return {
        "statusCode":      200,
        "lesson_type":     lesson_type,
        "items_selected":  selected_items,
        "cycle":           cycle,
        "telegram_msg_id": result["message_id"],
        "status":          result["status"],
        "phase":           "final - telegram delivery OK",
    }
