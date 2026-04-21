#!/usr/bin/env python3
"""
scripts/test_local.py
Prueba la Lambda localmente antes de hacer push.

Uso:
  # Probar verbos irregulares (mañana)
  python3 scripts/test_local.py --type irregular_verbs

  # Probar phrasal verbs (tarde)
  python3 scripts/test_local.py --type phrasal_verbs

Requisitos:
  - AWS CLI configurado con acceso a S3, DynamoDB y Bedrock
  - Variables de entorno configuradas (o usar --env dev)
  - pip install boto3
"""

import argparse
import json
import os
import sys

# Agregar src/ al path para importar los módulos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def main():
    parser = argparse.ArgumentParser(description="Test local del English Bot Lambda")
    parser.add_argument(
        "--type",
        choices=["irregular_verbs", "phrasal_verbs"],
        default="irregular_verbs",
        help="Tipo de lección a generar",
    )
    parser.add_argument(
        "--env",
        default="dev",
        help="Environment (default: dev)",
    )
    parser.add_argument(
        "--account-id",
        default=None,
        help="AWS Account ID (si no está en env vars)",
    )
    args = parser.parse_args()

    # ── Detectar Account ID ──────────────────────────────────────────────────
    account_id = args.account_id
    if not account_id:
        import boto3
        sts = boto3.client("sts")
        account_id = sts.get_caller_identity()["Account"]
        print(f"Account ID detectado: {account_id}")

    # ── Configurar variables de entorno ──────────────────────────────────────
    env = args.env
    os.environ.setdefault("S3_BUCKET",        f"english-bot-assets-{env}-{account_id}")
    os.environ.setdefault("DYNAMODB_TABLE",   f"english-bot-sent-log-{env}")
    os.environ.setdefault("AWS_REGION_NAME",  "us-east-1")
    os.environ.setdefault("BEDROCK_MODEL_ID", "amazon.nova-micro-v1:0")
    os.environ.setdefault("ENVIRONMENT",      env)

    print(f"\n{'='*60}")
    print(f"English Bot — Test Local")
    print(f"{'='*60}")
    print(f"Tipo:      {args.type}")
    print(f"Bucket:    {os.environ['S3_BUCKET']}")
    print(f"DynamoDB:  {os.environ['DYNAMODB_TABLE']}")
    print(f"Modelo:    {os.environ['BEDROCK_MODEL_ID']}")
    print(f"{'='*60}\n")

    # ── Simular el evento de EventBridge ────────────────────────────────────
    event = {
        "lesson_type": args.type,
        "schedule": "morning" if args.type == "irregular_verbs" else "afternoon",
    }

    # ── Invocar el handler ───────────────────────────────────────────────────
    from handler import lambda_handler

    print("Invocando lambda_handler...\n")
    result = lambda_handler(event, context=None)

    print(f"\n{'='*60}")
    print("RESULTADO:")
    print(f"{'='*60}")
    print(json.dumps(result, indent=2, ensure_ascii=False))

    print(f"\n{'='*60}")
    print("PREVIEW DEL MENSAJE WHATSAPP:")
    print(f"{'='*60}")
    print(result.get("message_preview", "Sin preview"))


if __name__ == "__main__":
    main()
