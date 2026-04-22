"""
handler.py — Fase 3
Orquestador principal de la Lambda del English Bot.

Flujo completo:
  1. Recibe evento de EventBridge Scheduler (lesson_type + schedule)
  2. VerbSelector elige 2 verbos sin repetir (S3 + DynamoDB)
  3. BedrockGenerator produce la explicación con Amazon Nova Micro
  4. WhatsAppSender envía el mensaje a WhatsApp vía Twilio
"""

import json
import logging
import os

from bedrock_generator import BedrockGenerator
from verb_selector import VerbSelector
from whatsapp_sender import WhatsAppSender

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# ── Variables de entorno ──────────────────────────────────────────────────────
S3_BUCKET        = os.environ["S3_BUCKET"]
DYNAMODB_TABLE   = os.environ["DYNAMODB_TABLE"]
AWS_REGION_NAME  = os.environ["AWS_REGION_NAME"]
BEDROCK_MODEL_ID = os.environ["BEDROCK_MODEL_ID"]
SSM_PREFIX       = os.environ["SSM_PREFIX"]
ENVIRONMENT      = os.environ.get("ENVIRONMENT", "dev")

# ── Clientes inicializados fuera del handler (reutilización entre invocaciones)
verb_selector = VerbSelector(
    s3_bucket      = S3_BUCKET,
    dynamodb_table = DYNAMODB_TABLE,
    aws_region     = AWS_REGION_NAME,
)

bedrock_generator = BedrockGenerator(
    model_id   = BEDROCK_MODEL_ID,
    aws_region = AWS_REGION_NAME,
)

whatsapp_sender = WhatsAppSender(
    ssm_prefix = SSM_PREFIX,
    aws_region = AWS_REGION_NAME,
)


def lambda_handler(event: dict, context) -> dict:
    logger.info("english-bot invocado | event: %s", json.dumps(event))

    # ── 1. Validar evento ─────────────────────────────────────────────────────
    lesson_type = event.get("lesson_type")
    schedule    = event.get("schedule")

    if lesson_type not in ("irregular_verbs", "phrasal_verbs"):
        raise ValueError(
            f"lesson_type inválido: '{lesson_type}'. "
            "Debe ser 'irregular_verbs' o 'phrasal_verbs'."
        )

    logger.info("Procesando lección — tipo: %s | horario: %s", lesson_type, schedule)

    # ── 2. Seleccionar verbos ─────────────────────────────────────────────────
    selected_verbs, cycle = verb_selector.select(lesson_type, count=2)
    logger.info("Verbos seleccionados: %s | Ciclo: %d", selected_verbs, cycle)

    # ── 3. Generar lección con Bedrock ────────────────────────────────────────
    lesson_content = bedrock_generator.generate(lesson_type, selected_verbs)

    # ── 4. Construir mensaje para WhatsApp ────────────────────────────────────
    whatsapp_message = bedrock_generator.build_whatsapp_message(
        lesson_type    = lesson_type,
        verbs          = selected_verbs,
        lesson_content = lesson_content,
        cycle          = cycle,
    )

    # ── 5. Enviar a WhatsApp vía Twilio ───────────────────────────────────────
    result = whatsapp_sender.send(whatsapp_message)

    logger.info(
        "Lección enviada — tipo: %s | verbos: %s | twilio_sid: %s",
        lesson_type, selected_verbs, result["sid"],
    )

    return {
        "statusCode":    200,
        "lesson_type":   lesson_type,
        "verbs_selected": selected_verbs,
        "cycle":         cycle,
        "twilio_sid":    result["sid"],
        "twilio_status": result["status"],
        "phase":         "3 - whatsapp delivery OK",
    }
