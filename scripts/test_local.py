#!/usr/bin/env python3
"""
scripts/test_local.py
Prueba la Lambda localmente antes de hacer push.

Uso:
  python3 scripts/test_local.py --type irregular_verbs
  python3 scripts/test_local.py --type phrasal_verbs
  python3 scripts/test_local.py --type irregular_verbs --dry-run  # sin enviar a WhatsApp
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def main():
    parser = argparse.ArgumentParser(description="Test local del English Bot Lambda")
    parser.add_argument(
        "--type",
        choices=["irregular_verbs", "phrasal_verbs"],
        default="irregular_verbs",
    )
    parser.add_argument("--env",        default="dev")
    parser.add_argument("--account-id", default=None)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Genera la lección pero NO envía el mensaje a WhatsApp",
    )
    args = parser.parse_args()

    # ── Detectar Account ID ──────────────────────────────────────────────────
    account_id = args.account_id
    if not account_id:
        import boto3
        account_id = boto3.client("sts").get_caller_identity()["Account"]
        print(f"Account ID detectado: {account_id}")

    env = args.env

    # ── Variables de entorno ─────────────────────────────────────────────────
    os.environ.setdefault("S3_BUCKET",        f"english-bot-assets-{env}-{account_id}")
    os.environ.setdefault("DYNAMODB_TABLE",   f"english-bot-sent-log-{env}")
    os.environ.setdefault("AWS_REGION_NAME",  "us-east-1")
    os.environ.setdefault("BEDROCK_MODEL_ID", "amazon.nova-micro-v1:0")
    os.environ.setdefault("SSM_PREFIX",       f"/english-bot/{env}")
    os.environ.setdefault("ENVIRONMENT",      env)

    print(f"\n{'='*60}")
    print(f"English Bot — Test Local {'(DRY RUN)' if args.dry_run else ''}")
    print(f"{'='*60}")
    print(f"Tipo:     {args.type}")
    print(f"Bucket:   {os.environ['S3_BUCKET']}")
    print(f"DynamoDB: {os.environ['DYNAMODB_TABLE']}")
    print(f"Modelo:   {os.environ['BEDROCK_MODEL_ID']}")
    print(f"SSM:      {os.environ['SSM_PREFIX']}")
    print(f"{'='*60}\n")

    if args.dry_run:
        # En dry-run probamos solo Bedrock + VerbSelector, sin Twilio
        print("Modo DRY RUN — no se enviará mensaje a WhatsApp\n")
        import boto3
        from verb_selector import VerbSelector
        from bedrock_generator import BedrockGenerator

        selector  = VerbSelector(
            s3_bucket      = os.environ["S3_BUCKET"],
            dynamodb_table = os.environ["DYNAMODB_TABLE"],
            aws_region     = os.environ["AWS_REGION_NAME"],
        )
        generator = BedrockGenerator(
            model_id   = os.environ["BEDROCK_MODEL_ID"],
            aws_region = os.environ["AWS_REGION_NAME"],
        )

        verbs, cycle    = selector.select(args.type, count=2)
        lesson_content  = generator.generate(args.type, verbs)
        message         = generator.build_whatsapp_message(args.type, verbs, lesson_content, cycle)

        print(f"Verbos seleccionados: {verbs} (ciclo {cycle})")
        print(f"\n{'='*60}")
        print("MENSAJE GENERADO:")
        print(f"{'='*60}")
        print(message)
        return

    # ── Test completo incluyendo envío a WhatsApp ────────────────────────────
    from handler import lambda_handler

    event = {
        "lesson_type": args.type,
        "schedule": "morning" if args.type == "irregular_verbs" else "afternoon",
    }

    print("Invocando lambda_handler (incluye envío a WhatsApp)...\n")
    result = lambda_handler(event, context=None)

    print(f"\n{'='*60}")
    print("RESULTADO:")
    print(f"{'='*60}")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
