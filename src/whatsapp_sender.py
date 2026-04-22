"""
whatsapp_sender.py
Envía mensajes de WhatsApp usando la API de Twilio.

Lee las credenciales desde SSM Parameter Store en cada instancia
(no en cada invocación — se cachean en el objeto para reutilización).

Twilio WhatsApp API:
  POST https://api.twilio.com/2010-04-01/Accounts/{SID}/Messages.json
  Body: From=whatsapp:+14155238886&To=whatsapp:+57XXX&Body=mensaje
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
        self._creds     = None   # cache de credenciales

    # ── Lee credenciales de SSM (una sola vez por instancia Lambda) ──────────
    def _load_credentials(self) -> dict:
        if self._creds:
            return self._creds

        params = [
            f"{self.ssm_prefix}/twilio_account_sid",
            f"{self.ssm_prefix}/twilio_auth_token",
            f"{self.ssm_prefix}/twilio_whatsapp_from",
            f"{self.ssm_prefix}/whatsapp_to",
        ]

        try:
            response = self.ssm.get_parameters(
                Names=params,
                WithDecryption=True,   # necesario para SecureString
            )

            if response.get("InvalidParameters"):
                raise ValueError(
                    f"Parámetros SSM no encontrados: {response['InvalidParameters']}"
                )

            creds = {p["Name"].split("/")[-1]: p["Value"] for p in response["Parameters"]}

            self._creds = {
                "account_sid": creds["twilio_account_sid"],
                "auth_token":  creds["twilio_auth_token"],
                "from_number": creds["twilio_whatsapp_from"],
                "to_number":   creds["whatsapp_to"],
            }

            logger.info(
                "Credenciales SSM cargadas — from: %s | to: %s",
                self._creds["from_number"],
                self._creds["to_number"],
            )

            return self._creds

        except ClientError as e:
            logger.error("Error leyendo SSM: %s", e)
            raise

    # ── Envía el mensaje via Twilio API usando urllib (sin dependencias extra) ─
    def send(self, message: str) -> dict:
        creds = self._load_credentials()

        url = (
            f"https://api.twilio.com/2010-04-01/Accounts/"
            f"{creds['account_sid']}/Messages.json"
        )

        # Twilio espera form-encoded, no JSON
        data = urllib.parse.urlencode({
            "From": creds["from_number"],
            "To":   creds["to_number"],
            "Body": message,
        }).encode("utf-8")

        # Basic Auth: Account SID + Auth Token en base64
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
                body   = json.loads(response.read().decode())
                msg_sid = body.get("sid", "unknown")

                logger.info(
                    "Mensaje enviado — SID: %s | status: %s | to: %s",
                    msg_sid,
                    body.get("status"),
                    creds["to_number"],
                )

                return {"sid": msg_sid, "status": body.get("status")}

        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            logger.error(
                "Twilio HTTP error %d: %s", e.code, error_body
            )
            raise RuntimeError(f"Twilio error {e.code}: {error_body}") from e
