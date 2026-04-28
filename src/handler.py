"""
handler.py — Fase 3 (multi-destinatario)
"""

import json
import logging
import os

from bedrock_generator import BedrockGenerator
from verb_selector import VerbSelector
from whatsapp_sender import WhatsAppSender

logger = logging.getLogger()
logger.setLevel(logging.INFO)

S3_BUCKET        = os.environ["S3_BUCKET"]
DYNAMODB_TABLE   = os.environ["DYNAMODB_TABLE"]
AWS_REGION_NAME  = os.environ["AWS_REGION_NAME"]
BEDROCK_MODEL_ID = os.environ["BEDROCK_MODEL_ID"]
SSM_PREFIX       = os.environ["SSM_PREFIX"]
ENVIRONMENT      = os.environ.get("ENVIRONMENT", "dev")

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

    lesson_type = event.get("lesson_type")
    schedule    = event.get("schedule")

    if lesson_type not in ("irregular_verbs", "phrasal_verbs", "vocabulary"):
        raise ValueError(f"lesson_type inválido: '{lesson_type}'.")

    logger.info("Procesando lección — tipo: %s | horario: %s", lesson_type, schedule)

    # 1. Seleccionar verbos
    selected_verbs, cycle = verb_selector.select(lesson_type, count=2)
    logger.info("Verbos seleccionados: %s | Ciclo: %d", selected_verbs, cycle)

    # 2. Generar lección con Bedrock
    lesson_content = bedrock_generator.generate(lesson_type, selected_verbs)

    # 3. Construir mensaje
    whatsapp_message = bedrock_generator.build_whatsapp_message(
        lesson_type    = lesson_type,
        verbs          = selected_verbs,
        lesson_content = lesson_content,
        cycle          = cycle,
    )

    # 4. Enviar a todos los destinatarios
    results    = whatsapp_sender.send(whatsapp_message)
    successful = [r for r in results if r["status"] != "failed"]
    failed     = [r for r in results if r["status"] == "failed"]

    logger.info(
        "Lección enviada — tipo: %s | verbos: %s | exitosos: %d | fallidos: %d",
        lesson_type, selected_verbs, len(successful), len(failed),
    )

    return {
        "statusCode":      200,
        "lesson_type":     lesson_type,
        "verbs_selected":  selected_verbs,
        "cycle":           cycle,
        "sent_count":      len(successful),
        "failed_count":    len(failed),
        "results":         results,
        "phase":           "3 - whatsapp multi-recipient OK",
    }
