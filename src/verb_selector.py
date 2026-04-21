"""
verb_selector.py
Lógica de selección aleatoria sin repetición.

Estrategia:
- DynamoDB guarda qué verbos ya fueron enviados en el "ciclo actual"
- Cuando se agotan todos los verbos de la lista, el ciclo se reinicia
- Cada invocación selecciona 2 verbos que no hayan salido en el ciclo

Estructura del item en DynamoDB:
  PK = "irregular_verbs" | "phrasal_verbs"
  SK = "state"
  sent    = ["be", "go", "have", ...]   # verbos ya enviados en este ciclo
  cycle   = 3                            # número de ciclo (para métricas)
  updated = "2025-03-20T13:00:00Z"
"""

import json
import logging
import random
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class VerbSelector:
    def __init__(self, s3_bucket: str, dynamodb_table: str, aws_region: str):
        self.s3 = boto3.client("s3", region_name=aws_region)
        self.dynamodb = boto3.resource("dynamodb", region_name=aws_region)
        self.table = self.dynamodb.Table(dynamodb_table)
        self.s3_bucket = s3_bucket

    # ── Carga la lista maestra desde S3 ──────────────────────────────────────
    def _load_list_from_s3(self, lesson_type: str) -> list[str]:
        key_map = {
            "irregular_verbs": "data/irregular_verbs.json",
            "phrasal_verbs":   "data/phrasal_verbs.json",
        }
        key = key_map.get(lesson_type)
        if not key:
            raise ValueError(f"lesson_type inválido: {lesson_type}")

        response = self.s3.get_object(Bucket=self.s3_bucket, Key=key)
        verbs = json.loads(response["Body"].read().decode("utf-8"))
        logger.info("Lista cargada desde S3: %s (%d verbos)", key, len(verbs))
        return verbs

    # ── Lee el estado actual del ciclo desde DynamoDB ────────────────────────
    def _get_state(self, lesson_type: str) -> dict:
        try:
            response = self.table.get_item(
                Key={"PK": lesson_type, "SK": "state"}
            )
            item = response.get("Item")
            if item:
                return {
                    "sent":  list(item.get("sent", [])),
                    "cycle": int(item.get("cycle", 1)),
                }
        except ClientError as e:
            logger.warning("Error leyendo estado DynamoDB: %s", e)

        # Estado inicial si no existe el item
        return {"sent": [], "cycle": 1}

    # ── Persiste el estado actualizado en DynamoDB ───────────────────────────
    def _save_state(self, lesson_type: str, sent: list[str], cycle: int):
        self.table.put_item(
            Item={
                "PK":      lesson_type,
                "SK":      "state",
                "sent":    sent,
                "cycle":   cycle,
                "updated": datetime.now(timezone.utc).isoformat(),
            }
        )
        logger.info(
            "Estado guardado — tipo: %s | enviados: %d | ciclo: %d",
            lesson_type, len(sent), cycle,
        )

    # ── Lógica principal: selecciona 2 verbos sin repetir ───────────────────
    def select(self, lesson_type: str, count: int = 2) -> tuple[list[str], int]:
        """
        Retorna (verbos_seleccionados, numero_de_ciclo).
        Si quedan menos verbos disponibles que `count`, reinicia el ciclo.
        """
        all_verbs = self._load_list_from_s3(lesson_type)
        state     = self._get_state(lesson_type)

        sent  = set(state["sent"])
        cycle = state["cycle"]

        # Verbos disponibles = lista completa menos los ya enviados
        available = [v for v in all_verbs if v not in sent]

        logger.info(
            "Disponibles: %d | Ya enviados: %d | Ciclo: %d",
            len(available), len(sent), cycle,
        )

        # Si quedan menos verbos que los necesarios → reiniciar ciclo
        if len(available) < count:
            logger.info("Lista agotada — reiniciando ciclo %d → %d", cycle, cycle + 1)
            available = list(all_verbs)
            sent  = set()
            cycle += 1

        # Selección aleatoria sin repetir
        selected = random.sample(available, count)

        # Actualizar estado
        new_sent = list(sent | set(selected))
        self._save_state(lesson_type, new_sent, cycle)

        return selected, cycle
