"""
whatsapp_sender.py
Envía mensajes de WhatsApp a múltiples destinatarios usando la API de Twilio.
"""

import logging
import urllib.request
import urllib.parse
import urllib.error
import base64
import json

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class WhatsAppSender:
    def __init__(self, ssm_prefix: str, aws_region: str):
        self.ssm        = boto3.client("ssm", region_name=aws_region)
        self.ssm_prefix = ssm_prefix
        self._creds     = None

    def _load_credentials(self) -> dict:
        if self._creds:
            return self._creds

        params = [
            f"{self.ssm_prefix}/twilio_account_sid",
            f"{self.ssm_prefix}/twilio_auth_token",
            f"{self.ssm_prefix}/twilio_whatsapp_from",
            f"{self.ssm_prefix}/whatsapp_recipients",
        ]

        try:
            response = self.ssm.get_parameters(
                Names=params,
                WithDecryption=True,
            )

            if response.get("InvalidParameters"):
                raise ValueError(
                    f"Parámetros SSM no encontrados: {response['InvalidParameters']}"
                )

            creds = {p["Name"].split("/")[-1]: p["Value"] for p in response["Parameters"]}

            recipients = [
                r.strip()
                for r in creds["whatsapp_recipients"].split(",")
                if r.strip()
            ]

            self._creds = {
                "account_sid": creds["twilio_account_sid"],
                "auth_token":  creds["twilio_auth_token"],
                "from_number": creds["twilio_whatsapp_from"],
                "recipients":  recipients,
            }

            logger.info(
                "Credenciales SSM cargadas — from: %s | destinatarios: %d",
                self._creds["from_number"],
                len(recipients),
            )

            return self._creds

        except ClientError as e:
            logger.error("Error leyendo SSM: %s", e)
            raise

    def _send_to_number(self, message: str, to_number: str, creds: dict) -> dict:
        url = (
            f"https://api.twilio.com/2010-04-01/Accounts/"
            f"{creds['account_sid']}/Messages.json"
        )

        data = urllib.parse.urlencode({
            "From": creds["from_number"],
            "To":   to_number,
            "Body": message,
        }).encode("utf-8")

        credentials = base64.b64encode(
            f"{creds['account_sid']}:{creds['auth_token']}".encode()
        ).decode()

        request = urllib.request.Request(
            url,
            data=data,
            headers={
                "Authorization": f"Basic {credentials}",
                "Content-Type":  "application/x-www-form-urlencoded",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                body = json.loads(response.read().decode())
                logger.info(
                    "Enviado — SID: %s | status: %s | to: %s | chars: %d",
                    body.get("sid"), body.get("status"), to_number, len(message),
                )
                return {"to": to_number, "sid": body.get("sid"), "status": body.get("status")}

        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            logger.error("Twilio error %d para %s: %s", e.code, to_number, error_body)
            return {"to": to_number, "sid": None, "status": "failed", "error": error_body}

    def send(self, message: str) -> list[dict]:
        """Envía el mensaje a todos los destinatarios."""
        creds   = self._load_credentials()
        results = []

        logger.info("Enviando mensaje de %d chars a %d destinatarios", len(message), len(creds["recipients"]))

        for recipient in creds["recipients"]:
            result = self._send_to_number(message, recipient, creds)
            results.append(result)

        successful = [r for r in results if r["status"] != "failed"]
        failed     = [r for r in results if r["status"] == "failed"]

        logger.info(
            "Envío completado — exitosos: %d | fallidos: %d",
            len(successful), len(failed),
        )

        if failed:
            logger.warning("Fallaron: %s", [r["to"] for r in failed])

        return results
