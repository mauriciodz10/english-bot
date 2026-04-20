"""
handler.py — Placeholder de la Lambda para Fase 1.

En Fase 2 este archivo se reemplaza con la lógica real:
  - Consultar S3 para obtener la lista de verbos
  - Consultar DynamoDB para saber cuáles ya se enviaron
  - Llamar a Amazon Bedrock para generar la explicación
  - Llamar a Twilio para enviar el mensaje a WhatsApp
"""

import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    logger.info("english-bot invocado | event: %s", json.dumps(event))

    lesson_type = event.get("lesson_type", "unknown")
    schedule    = event.get("schedule", "unknown")

    logger.info("Tipo de lección: %s | Horario: %s", lesson_type, schedule)

    # Fase 1: solo confirmamos que la infraestructura dispara correctamente
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": f"Placeholder OK — lesson_type={lesson_type}, schedule={schedule}",
            "phase": "1 - infrastructure only"
        })
    }
