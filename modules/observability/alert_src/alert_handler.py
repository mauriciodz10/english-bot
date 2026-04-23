"""
alert_handler.py
Lambda invocada por SNS cuando una alarma de CloudWatch dispara.
Envía un mensaje de alerta a todos los destinatarios de WhatsApp.
"""

import json
import logging
import os
import urllib.request
import urllib.parse
import urllib.error
import base64

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

SSM_PREFIX = os.environ["SSM_PREFIX"]


def _get_twilio_creds() -> dict:
    ssm = boto3.client("ssm", region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"))

    params = [
        f"{SSM_PREFIX}/twilio_account_sid",
        f"{SSM_PREFIX}/twilio_auth_token",
        f"{SSM_PREFIX}/twilio_whatsapp_from",
        f"{SSM_PREFIX}/whatsapp_recipients",
    ]

    response = ssm.get_parameters(Names=params, WithDecryption=True)
    creds    = {p["Name"].split("/")[-1]: p["Value"] for p in response["Parameters"]}

    return {
        "account_sid": creds["twilio_account_sid"],
        "auth_token":  creds["twilio_auth_token"],
        "from_number": creds["twilio_whatsapp_from"],
        "recipients":  [r.strip() for r in creds["whatsapp_recipients"].split(",") if r.strip()],
    }


def _send_whatsapp(message: str, creds: dict):
    url = (
        f"https://api.twilio.com/2010-04-01/Accounts/"
        f"{creds['account_sid']}/Messages.json"
    )
    credentials = base64.b64encode(
        f"{creds['account_sid']}:{creds['auth_token']}".encode()
    ).decode()

    for recipient in creds["recipients"]:
        data = urllib.parse.urlencode({
            "From": creds["from_number"],
            "To":   recipient,
            "Body": message,
        }).encode("utf-8")

        request = urllib.request.Request(
            url, data=data,
            headers={
                "Authorization": f"Basic {credentials}",
                "Content-Type":  "application/x-www-form-urlencoded",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=10) as resp:
                body = json.loads(resp.read().decode())
                logger.info("Alerta enviada a %s — SID: %s", recipient, body.get("sid"))
        except urllib.error.HTTPError as e:
            logger.error("Error enviando alerta a %s: %s", recipient, e.read().decode())


def _parse_alarm(sns_message: str) -> dict:
    """Extrae los campos relevantes del mensaje de CloudWatch Alarm."""
    try:
        alarm = json.loads(sns_message)
        return {
            "name":        alarm.get("AlarmName", "Desconocida"),
            "description": alarm.get("AlarmDescription", "Sin descripción"),
            "state":       alarm.get("NewStateValue", "UNKNOWN"),
            "reason":      alarm.get("NewStateReason", "Sin detalle"),
        }
    except json.JSONDecodeError:
        return {
            "name":        "Alarma",
            "description": sns_message[:200],
            "state":       "UNKNOWN",
            "reason":      "",
        }


def lambda_handler(event, context):
    logger.info("Alert handler invocado | event: %s", json.dumps(event))

    for record in event.get("Records", []):
        sns_message = record["Sns"]["Message"]
        alarm       = _parse_alarm(sns_message)

        # Emoji según el estado de la alarma
        if alarm["state"] == "ALARM":
            emoji  = "🚨"
            status = "FALLO DETECTADO"
        elif alarm["state"] == "OK":
            emoji  = "✅"
            status = "RECUPERADO"
        else:
            emoji  = "⚠️"
            status = alarm["state"]

        message = (
            f"{emoji} *English Bot — {status}*\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"📋 *Alarma:* {alarm['name']}\n"
            f"📝 *Detalle:* {alarm['description']}\n"
            f"🔍 *Razón:* {alarm['reason'][:200]}\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"_English Bot Monitor 🤖_"
        )

        logger.info("Enviando alerta: %s", alarm["name"])

        try:
            creds = _get_twilio_creds()
            _send_whatsapp(message, creds)
        except Exception as e:
            logger.error("Error enviando alerta WhatsApp: %s", e)
            # No relanzamos — el email SNS ya fue enviado como fallback

    return {"statusCode": 200}
