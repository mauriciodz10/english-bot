"""
handler.py — Fase 2
Orquestador principal de la Lambda del English Bot.

Flujo de ejecución:
  1. Recibe el evento de EventBridge Scheduler (lesson_type + schedule)
  2. VerbSelector elige 2 verbos/phrasal verbs sin repetir (desde S3 + DynamoDB)
  3. BedrockGenerator produce la explicación formateada
  4. Loguea el mensaje generado (Fase 3 lo enviará a WhatsApp vía Twilio)
"""

import json
import logging
import os

from bedrock_generator import BedrockGenerator
from verb_selector import VerbSelector

# ── Configuración de logging estructurado ────────────────────────────────────
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# ── Variables de entorno (inyectadas por Terraform) ──────────────────────────
S3_BUCKET        = os.environ["S3_BUCKET"]
DYNAMODB_TABLE   = os.environ["DYNAMODB_TABLE"]
AWS_REGION_NAME  = os.environ["AWS_REGION_NAME"]
BEDROCK_MODEL_ID = os.environ["BEDROCK_MODEL_ID"]
ENVIRONMENT      = os.environ.get("ENVIRONMENT", "dev")

# ── Inicializar clientes fuera del handler (reutilización entre invocaciones) ─
verb_selector = VerbSelector(
    s3_bucket      = S3_BUCKET,
    dynamodb_table = DYNAMODB_TABLE,
    aws_region     = AWS_REGION_NAME,
)

bedrock_generator = BedrockGenerator(
    model_id   = BEDROCK_MODEL_ID,
    aws_region = AWS_REGION_NAME,
)


def lambda_handler(event: dict, context) -> dict:
    logger.info("english-bot invocado | event: %s", json.dumps(event))

    # ── 1. Validar el evento ──────────────────────────────────────────────────
    lesson_type = event.get("lesson_type")
    schedule    = event.get("schedule")

    if lesson_type not in ("irregular_verbs", "phrasal_verbs"):
        raise ValueError(
            f"lesson_type inválido: '{lesson_type}'. "
            "Debe ser 'irregular_verbs' o 'phrasal_verbs'."
        )

    logger.info("Procesando lección — tipo: %s | horario: %s", lesson_type, schedule)

    # ── 2. Seleccionar verbos sin repetir ─────────────────────────────────────
    selected_verbs, cycle = verb_selector.select(lesson_type, count=2)
    logger.info("Verbos seleccionados: %s | Ciclo: %d", selected_verbs, cycle)

    # ── 3. Generar lección con Bedrock ────────────────────────────────────────
    lesson_content = bedrock_generator.generate(lesson_type, selected_verbs)

    # ── 4. Construir mensaje formateado para WhatsApp ─────────────────────────
    whatsapp_message = bedrock_generator.build_whatsapp_message(
        lesson_type    = lesson_type,
        verbs          = selected_verbs,
        lesson_content = lesson_content,
        cycle          = cycle,
    )

    logger.info("Mensaje generado:\n%s", whatsapp_message)

    # ── 5. Retornar resultado (Fase 3 agrega el envío a WhatsApp aquí) ────────
    return {
        "statusCode": 200,
        "lesson_type":     lesson_type,
        "verbs_selected":  selected_verbs,
        "cycle":           cycle,
        "message_preview": whatsapp_message[:200] + "...",
        "phase":           "2 - bedrock generation OK",
    }
