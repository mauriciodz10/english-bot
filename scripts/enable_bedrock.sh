#!/bin/bash
# scripts/enable_bedrock.sh
# Verifica y habilita el modelo Claude Haiku en Amazon Bedrock (us-east-1)
# Debe correrse UNA VEZ antes de hacer el primer deploy de Fase 2.

set -e

REGION="us-east-1"
MODEL_ID="anthropic.claude-haiku-4-5-20251001"

echo "=== Verificando acceso a Amazon Bedrock ==="
echo "Región: $REGION"
echo "Modelo: $MODEL_ID"
echo ""

# Verificar si el modelo ya está habilitado
STATUS=$(aws bedrock get-foundation-model-availability \
  --model-id "$MODEL_ID" \
  --region "$REGION" \
  --query "agreementAvailability.status" \
  --output text 2>/dev/null || echo "UNAVAILABLE")

if [ "$STATUS" = "AVAILABLE" ]; then
  echo "✓ El modelo ya está habilitado. Listo para la Fase 2."
  exit 0
fi

echo "El modelo no está habilitado aún."
echo ""
echo "Pasos para habilitarlo (requiere consola AWS):"
echo ""
echo "1. Ve a: https://us-east-1.console.aws.amazon.com/bedrock/home?region=us-east-1#/modelaccess"
echo "2. Haz clic en 'Manage model access'"
echo "3. Busca 'Claude Haiku' en la sección Anthropic"
echo "4. Marca el checkbox y haz clic en 'Save changes'"
echo "5. Espera ~1 minuto y vuelve a correr este script"
echo ""
echo "Alternativamente, prueba con AWS CLI:"
echo "  aws bedrock put-model-invocation-logging-configuration --region $REGION"
echo ""

# Test rápido de invocación para confirmar acceso
echo "=== Probando invocación del modelo ==="
RESPONSE=$(aws bedrock-runtime invoke-model \
  --model-id "$MODEL_ID" \
  --region "$REGION" \
  --content-type "application/json" \
  --accept "application/json" \
  --body '{"anthropic_version":"bedrock-2023-05-31","max_tokens":50,"messages":[{"role":"user","content":"Di hola en una palabra"}]}' \
  /tmp/bedrock_test_output.json 2>&1) || {
    echo "✗ Error al invocar el modelo. Verifica que esté habilitado en la consola."
    echo "Error: $RESPONSE"
    exit 1
  }

RESULT=$(cat /tmp/bedrock_test_output.json | python3 -c "
import json, sys
body = json.load(sys.stdin)
print(body['content'][0]['text'])
")

echo "✓ Modelo responde correctamente: '$RESULT'"
echo ""
echo "=== Bedrock listo para Fase 2 ==="
