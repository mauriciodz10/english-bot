"""
telegram_sender.py
Envía mensajes al grupo de Telegram usando la Bot API.

Sin ventanas de mensajería ni aprobaciones — el bot envía cuando quiera.
Lee las credenciales desde SSM Parameter Store.

Telegram Bot API:
  POST https://api.telegram.org/bot{TOKEN}/sendMessage
  Body: chat_id=-100XXXXXXX&text=mensaje&parse_mode=Markdown
"""

import json
import logging
import urllib.request
import urllib.parse
import urllib.error

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org"


class TelegramSender:
    def __init__(self, ssm_prefix: str, aws_region: str):
        self.ssm        = boto3.client("ssm", region_name=aws_region)
        self.ssm_prefix = ssm_prefix
        self._creds     = None

    # ── Lee credenciales de SSM (una sola vez por instancia Lambda) ──────────
    def _load_credentials(self) -> dict:
        if self._creds:
            return self._creds

        params = [
            f"{self.ssm_prefix}/telegram_bot_token",
            f"{self.ssm_prefix}/telegram_chat_id",
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

            self._creds = {
                "token":   creds["telegram_bot_token"],
                "chat_id": creds["telegram_chat_id"],
            }

            logger.info(
                "Credenciales Telegram cargadas — chat_id: %s",
                self._creds["chat_id"],
            )

            return self._creds

        except ClientError as e:
            logger.error("Error leyendo SSM: %s", e)
            raise

    def send(self, message: str) -> dict:
        """
        Envía el mensaje al grupo de Telegram.
        Usa parse_mode=Markdown para que *negrita* y _itálica_ funcionen.
        """
        creds = self._load_credentials()

        url  = f"{TELEGRAM_API}/bot{creds['token']}/sendMessage"
        data = urllib.parse.urlencode({
            "chat_id":    creds["chat_id"],
            "text":       message,
            "parse_mode": "Markdown",
        }).encode("utf-8")

        request = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                body    = json.loads(response.read().decode())
                msg_id  = body["result"]["message_id"]

                logger.info(
                    "Mensaje enviado a Telegram — message_id: %s | chat_id: %s | chars: %d",
                    msg_id, creds["chat_id"], len(message),
                )

                return {"message_id": msg_id, "status": "sent"}

        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            logger.error("Telegram HTTP error %d: %s", e.code, error_body)
            raise RuntimeError(f"Telegram error {e.code}: {error_body}") from e
